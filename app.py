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
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_session = None
sessions_dir = Path("sessions")
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
        socketio.emit('progress', {
            'stage': 1,
            'message': 'Starting idea generation...',
            'progress': 0
        }, broadcast=True)

        # Paths to programs
        scripts_dir = Path(__file__).parent.parent
        idea_generator_path = scripts_dir / "DocIdeaGenerator" / "cli.py"

        if not idea_generator_path.exists():
            raise FileNotFoundError(f"DocIdeaGenerator not found at {idea_generator_path}")

        # Create session directory
        session_dir = sessions_dir / session.session_id
        session_dir.mkdir(exist_ok=True)
        topics_dir = session_dir / "topics"
        topics_dir.mkdir(exist_ok=True)

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
            if config['idea_generation'].get('start_date'):
                cmd.extend(["--start-date", config['idea_generation']['start_date']])
            if config['idea_generation'].get('label'):
                cmd.extend(["--label", config['idea_generation']['label']])
            if config['idea_generation'].get('focus'):
                cmd.extend(["--focus", config['idea_generation']['focus']])
            if config['idea_generation'].get('combined_topics'):
                cmd.append("--combined-topics")

            socketio.emit('progress', {
                'stage': 1,
                'message': 'Running DocIdeaGenerator...',
                'progress': 25
            }, broadcast=True)

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
            print(f"DocIdeaGenerator stdout: {result.stdout}")
            print(f"DocIdeaGenerator stderr: {result.stderr}")
            print(f"DocIdeaGenerator return code: {result.returncode}")

            # Check if DocIdeaGenerator failed
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                raise RuntimeError(f"DocIdeaGenerator failed with return code {result.returncode}: {error_msg}")

            socketio.emit('progress', {
                'stage': 1,
                'message': 'Analyzing generated topics...',
                'progress': 75
            }, broadcast=True)

            # Find generated topic files
            topic_files = list(idea_gen_dir.glob("topic_*.md"))
            if not topic_files:
                topic_files = list(idea_gen_dir.glob("analysis_*.md"))

            if not topic_files:
                raise RuntimeError("No topic files generated. DocIdeaGenerator may have run in interactive mode and failed to generate topics.")

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

            socketio.emit('progress', {
                'stage': 1,
                'message': f'Generated {len(topics)} topics. Ready for review.',
                'progress': 100,
                'complete': True
            }, broadcast=True)

            socketio.emit('stage1_complete', {
                'topics': topics,
                'count': len(topics)
            }, broadcast=True)

        finally:
            os.chdir(original_cwd)

    except Exception as e:
        session.status = 'error'
        session.error = str(e)
        socketio.emit('error', {
            'stage': 1,
            'message': f'Error in Stage 1: {str(e)}'
        }, broadcast=True)


def run_stage2(session: OrchestratorSession):
    """Run PersonalizedDocGenerator (Stage 2)"""
    try:
        selected = session.selected_topics
        total = len(selected)

        socketio.emit('progress', {
            'stage': 2,
            'message': f'Generating {total} documents...',
            'progress': 0
        }, broadcast=True)

        # Paths
        scripts_dir = Path(__file__).parent.parent
        doc_generator_path = scripts_dir / "PersonalizedDocGenerator" / "document_generator.py"

        if not doc_generator_path.exists():
            raise FileNotFoundError(f"PersonalizedDocGenerator not found at {doc_generator_path}")

        config = session.config
        mode = config['document_generation'].get('mode', config['global']['mode'])
        documents = []

        for i, topic in enumerate(selected, 1):
            socketio.emit('progress', {
                'stage': 2,
                'message': f'Generating document {i}/{total}: {topic["title"][:40]}...',
                'progress': int((i-1) / total * 100),
                'current': i,
                'total': total
            }, broadcast=True)

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
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config['orchestration']['stage2_timeout']
            )

            if result.returncode == 0:
                documents.append({
                    'topic': topic['title'],
                    'status': 'success',
                    'output': result.stdout
                })
            else:
                documents.append({
                    'topic': topic['title'],
                    'status': 'failed',
                    'error': result.stderr[:200]
                })

        session.stage2_results = documents
        session.status = 'completed'

        successful = len([d for d in documents if d['status'] == 'success'])

        socketio.emit('progress', {
            'stage': 2,
            'message': f'Completed! {successful}/{total} documents generated.',
            'progress': 100,
            'complete': True
        }, broadcast=True)

        socketio.emit('stage2_complete', {
            'documents': documents,
            'successful': successful,
            'total': total
        }, broadcast=True)

    except Exception as e:
        session.status = 'error'
        session.error = str(e)
        socketio.emit('error', {
            'stage': 2,
            'message': f'Error in Stage 2: {str(e)}'
        }, broadcast=True)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 WebDocOrchestrator Starting")
    print("=" * 60)
    print("\nOpen your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
