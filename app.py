#!/usr/bin/env python3
"""
WebDocOrchestrator - Web-based Content Generation Pipeline

A modern web dashboard for orchestrating DocIdeaGenerator and PersonalizedDocGenerator
with real-time progress updates and interactive topic selection.
"""

import os
import sys
import json
import yaml
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Setup logging
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_session = None
# Use absolute path for sessions directory to avoid issues when changing cwd
sessions_dir = Path(__file__).parent / "sessions"
sessions_dir.mkdir(exist_ok=True)


@dataclass
class OrchestratorSession:
    """Represents an orchestration session"""
    session_id: str
    config: Dict
    status: str  # 'configuring', 'stage1', 'reviewing', 'stage2', 'completed', 'error'
    stage1_results: Optional[Dict] = None
    selected_topics: Optional[List[Dict]] = None
    stage2_results: Optional[List[Dict]] = None
    error: Optional[str] = None


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/api/config/example', methods=['GET'])
def get_example_config():
    """Get example configuration"""
    example_config = {
        'name': 'My Content Pipeline',
        'global': {'mode': 'test'},
        'idea_generation': {
            'source': 'gmail',
            'start_date': '01012025',
            'label': 'AIQ',
            'focus': 'AI transformation and business strategy',
            'combined_topics': False
        },
        'document_generation': {
            'style': '',
            'audience': 'business executives',
            'type': 'blog post',
            'size': '800 words',
            'customer_story': '',
            'output': './output'
        },
        'orchestration': {
            'stage1_timeout': 600,
            'stage2_timeout': 300,
            'retry_on_failure': True
        }
    }
    return jsonify(example_config)


@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a new orchestration session"""
    global current_session

    config = request.json

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting new session {session_id}")

    current_session = OrchestratorSession(
        session_id=session_id,
        config=config,
        status='stage1'
    )

    # Start stage 1 in background thread
    thread = threading.Thread(target=run_stage1, args=(current_session,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'session_id': session_id,
        'status': 'started'
    })


@app.route('/api/session/status', methods=['GET'])
def get_session_status():
    """Get current session status"""
    global current_session

    if not current_session:
        return jsonify({'status': 'no_session'})

    return jsonify({
        'session_id': current_session.session_id,
        'status': current_session.status,
        'stage1_results': current_session.stage1_results,
        'selected_topics': current_session.selected_topics,
        'stage2_results': current_session.stage2_results,
        'error': current_session.error
    })


@app.route('/api/topics/select', methods=['POST'])
def select_topics():
    """Select topics for document generation"""
    global current_session

    if not current_session or current_session.status != 'reviewing':
        return jsonify({'error': 'Invalid session state'}), 400

    selected_indices = request.json.get('selected', [])
    topics = current_session.stage1_results.get('topics', [])

    current_session.selected_topics = [topics[i] for i in selected_indices]
    current_session.status = 'stage2'

    # Start stage 2 in background thread
    thread = threading.Thread(target=run_stage2, args=(current_session,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'started',
        'count': len(current_session.selected_topics)
    })


def run_stage1(session: OrchestratorSession):
    """Run DocIdeaGenerator (Stage 1)"""
    try:
        logger.info(f"Starting Stage 1 for session {session.session_id}")
        socketio.emit('progress', {
            'stage': 1,
            'message': 'Starting idea generation...',
            'progress': 0
        })

        # Paths to programs
        scripts_dir = Path(__file__).parent.parent
        idea_generator_path = scripts_dir / "DocIdeaGenerator" / "cli.py"

        if not idea_generator_path.exists():
            error_msg = f"DocIdeaGenerator not found at {idea_generator_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Create session directory
        session_dir = sessions_dir / session.session_id
        session_dir.mkdir(exist_ok=True)
        topics_dir = session_dir / "topics"
        topics_dir.mkdir(exist_ok=True)
        logger.info(f"Session directory: {session_dir.absolute()}")
        logger.info(f"Topics directory: {topics_dir.absolute()}")

        # Change to DocIdeaGenerator directory
        idea_gen_dir = idea_generator_path.parent
        original_cwd = Path.cwd()
        os.chdir(idea_gen_dir)

        try:
            # Build command
            config = session.config
            cmd = [
                "python3", str(idea_generator_path),
                "--mode", config['global']['mode'],
                "--source", config['idea_generation']['source'],
                "--save-local"
            ]

            # Add optional arguments
            if config['idea_generation'].get('email'):
                # Process specific email
                cmd.extend(["--email", config['idea_generation']['email']])
                cmd.append("--yes")  # Auto-confirm for single email
                logger.info(f"Processing specific email: {config['idea_generation']['email']}")
            else:
                # Batch process all emails
                cmd.append("--batch")
                logger.info("No email specified - batch processing all emails matching criteria")
            if config['idea_generation'].get('start_date'):
                cmd.extend(["--start-date", config['idea_generation']['start_date']])
            if config['idea_generation'].get('label'):
                cmd.extend(["--label", config['idea_generation']['label']])
            if config['idea_generation'].get('focus'):
                cmd.extend(["--focus", config['idea_generation']['focus']])
            if config['idea_generation'].get('combined_topics'):
                cmd.append("--combined-topics")

            logger.info(f"Running DocIdeaGenerator with command: {' '.join(cmd)}")

            socketio.emit('progress', {
                'stage': 1,
                'message': 'Running DocIdeaGenerator...',
                'progress': 25
            })

            # Run DocIdeaGenerator in non-interactive mode
            # Note: If no --email is specified, DocIdeaGenerator will try to be interactive
            # We need to provide stdin=DEVNULL to prevent hanging
            # TODO: Add --batch mode to DocIdeaGenerator for non-interactive processing
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=config['orchestration']['stage1_timeout']
            )

            # Log the output for debugging
            logger.info(f"DocIdeaGenerator return code: {result.returncode}")
            if result.stdout:
                logger.info(f"DocIdeaGenerator stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"DocIdeaGenerator stderr: {result.stderr}")

            # Check if DocIdeaGenerator failed
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                logger.error(f"DocIdeaGenerator failed with return code {result.returncode}: {error_msg}")
                raise RuntimeError(f"DocIdeaGenerator failed with return code {result.returncode}: {error_msg}")

            socketio.emit('progress', {
                'stage': 1,
                'message': 'Analyzing generated topics...',
                'progress': 75
            })

            # Find generated topic files
            logger.info(f"Searching for topic files in {idea_gen_dir}")
            topic_files = list(idea_gen_dir.glob("topic_*.md"))
            if not topic_files:
                topic_files = list(idea_gen_dir.glob("analysis_*.md"))

            if not topic_files:
                error_msg = "No topic files generated. DocIdeaGenerator may have run in interactive mode and failed to generate topics."
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info(f"Found {len(topic_files)} topic files")

            # Move files and parse
            topics = []
            for i, file_path in enumerate(topic_files):
                with open(file_path, 'r') as f:
                    content = f.read()

                # Extract title
                lines = content.split('\n')
                title = file_path.stem.replace('_', ' ').title()
                for line in lines:
                    if line.startswith('#'):
                        title = line.lstrip('#').strip()
                        break

                # Move to session topics directory
                dest_path = topics_dir / file_path.name
                import shutil
                logger.info(f"Moving file from {file_path} to {dest_path}")
                shutil.move(str(file_path), str(dest_path))

                topics.append({
                    'id': i,
                    'title': title,
                    'file_path': str(dest_path),
                    'preview': content[:300],
                    'word_count': len(content.split())
                })

            session.stage1_results = {
                'topics': topics,
                'count': len(topics),
                'timestamp': datetime.now().isoformat()
            }
            session.status = 'reviewing'

            logger.info(f"Stage 1 completed successfully. Generated {len(topics)} topics")

            socketio.emit('progress', {
                'stage': 1,
                'message': f'Generated {len(topics)} topics. Ready for review.',
                'progress': 100,
                'complete': True
            })

            socketio.emit('stage1_complete', {
                'topics': topics,
                'count': len(topics)
            })

        finally:
            os.chdir(original_cwd)

    except Exception as e:
        logger.error(f"Stage 1 failed: {str(e)}", exc_info=True)
        session.status = 'error'
        session.error = str(e)
        socketio.emit('error', {
            'stage': 1,
            'message': f'Error in Stage 1: {str(e)}'
        })


def run_stage2(session: OrchestratorSession):
    """Run PersonalizedDocGenerator (Stage 2)"""
    try:
        logger.info(f"Starting Stage 2 for session {session.session_id}")
        selected = session.selected_topics
        total = len(selected)

        logger.info(f"Generating {total} documents")

        socketio.emit('progress', {
            'stage': 2,
            'message': f'Generating {total} documents...',
            'progress': 0
        })

        # Paths
        scripts_dir = Path(__file__).parent.parent
        doc_generator_path = scripts_dir / "PersonalizedDocGenerator" / "document_generator.py"

        if not doc_generator_path.exists():
            raise FileNotFoundError(f"PersonalizedDocGenerator not found at {doc_generator_path}")

        config = session.config
        mode = config['document_generation'].get('mode', config['global']['mode'])
        documents = []

        for i, topic in enumerate(selected, 1):
            logger.info(f"Processing document {i}/{total}: {topic['title']}")
            socketio.emit('progress', {
                'stage': 2,
                'message': f'Generating document {i}/{total}: {topic["title"][:40]}...',
                'progress': int((i-1) / total * 100),
                'current': i,
                'total': total
            })

            # Build command
            cmd = [
                "python3", str(doc_generator_path),
                "--mode", mode,
                "--topic", topic['file_path'],
                "--audience", config['document_generation']['audience'],
                "--type", config['document_generation']['type'],
                "--size", config['document_generation']['size'],
                "--output", config['document_generation']['output']
            ]

            if config['document_generation'].get('style'):
                cmd.extend(["--style", config['document_generation']['style']])
            if config['document_generation'].get('customer_story'):
                cmd.extend(["--customer-story", config['document_generation']['customer_story']])

            # Run document generator
            logger.info(f"Running PersonalizedDocGenerator with command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config['orchestration']['stage2_timeout']
            )

            if result.returncode == 0:
                logger.info(f"Document '{topic['title']}' generated successfully")
                documents.append({
                    'topic': topic['title'],
                    'status': 'success',
                    'output': result.stdout
                })
            else:
                logger.error(f"Document '{topic['title']}' failed: {result.stderr[:200]}")
                documents.append({
                    'topic': topic['title'],
                    'status': 'failed',
                    'error': result.stderr[:200]
                })

        session.stage2_results = documents
        session.status = 'completed'

        successful = len([d for d in documents if d['status'] == 'success'])

        logger.info(f"Stage 2 completed. {successful}/{total} documents generated successfully")

        socketio.emit('progress', {
            'stage': 2,
            'message': f'Completed! {successful}/{total} documents generated.',
            'progress': 100,
            'complete': True
        })

        socketio.emit('stage2_complete', {
            'documents': documents,
            'successful': successful,
            'total': total
        })

    except Exception as e:
        logger.error(f"Stage 2 failed: {str(e)}", exc_info=True)
        session.status = 'error'
        session.error = str(e)
        socketio.emit('error', {
            'stage': 2,
            'message': f'Error in Stage 2: {str(e)}'
        })


@socketio.on('connect')
def handle_connect():
    """Handle client connection and sync with current session state"""
    logger.info('Client connected')
    emit('connected', {'status': 'ok'})

    # If there's an active session, sync the reconnected client with current state
    global current_session
    if current_session:
        logger.info(f"Syncing reconnected client with session {current_session.session_id}, status: {current_session.status}")

        if current_session.status == 'reviewing' and current_session.stage1_results:
            # Stage 1 completed, send results to client
            logger.info("Sending stage1_complete event to reconnected client")
            emit('stage1_complete', {
                'topics': current_session.stage1_results['topics'],
                'count': current_session.stage1_results['count']
            })
        elif current_session.status == 'completed' and current_session.stage2_results:
            # Stage 2 completed, send results
            logger.info("Sending stage2_complete event to reconnected client")
            documents = current_session.stage2_results
            successful = len([d for d in documents if d['status'] == 'success'])
            emit('stage2_complete', {
                'documents': documents,
                'successful': successful,
                'total': len(documents)
            })
        elif current_session.status == 'error':
            # Session has an error
            logger.info("Sending error event to reconnected client")
            emit('error', {
                'stage': 1 if not current_session.stage1_results else 2,
                'message': current_session.error
            })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 WebDocOrchestrator Starting")
    print("=" * 60)
    print("\nOpen your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
