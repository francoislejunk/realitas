"""
Storage utilities for enhanced UTAS session management.
Provides compression, indexing, and archival capabilities.
"""

import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional


class EnhancedSessionStorage:
    """Enhanced storage utilities for UTAS sessions."""
    
    def __init__(self, storage_directory: str = "simulation_data"):
        self.storage_directory = Path(storage_directory)
        self.sessions_directory = self.storage_directory / "sessions"
        self.archive_directory = self.storage_directory / "archive"
        self.index_file = self.storage_directory / "session_index.json"
        
        for directory in [self.sessions_directory, self.archive_directory]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_session_compressed(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data with optional compression for large sessions."""
        session_file = self.sessions_directory / f"session_{session_id}.json"
        
        json_str = json.dumps(session_data, indent=2, ensure_ascii=False)
        
        if len(json_str.encode('utf-8')) > 100 * 1024:
            compressed_file = self.sessions_directory / f"session_{session_id}.json.gz"
            with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
                f.write(json_str)
            
            if session_file.exists():
                session_file.unlink()
        else:
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            compressed_file = self.sessions_directory / f"session_{session_id}.json.gz"
            if compressed_file.exists():
                compressed_file.unlink()
        
        self._update_session_index(session_id, session_data)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data, handling both compressed and uncompressed files."""
        compressed_file = self.sessions_directory / f"session_{session_id}.json.gz"
        if compressed_file.exists():
            try:
                with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading compressed session {session_id}: {e}")
        
        session_file = self.sessions_directory / f"session_{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
        
        return None
    
    def _update_session_index(self, session_id: str, session_data: Dict[str, Any]):
        """Maintain a lightweight index of all sessions for fast listing."""
        index = {}
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except:
                index = {}
        
        sim_session = session_data.get('simulation_session', {})
        index[session_id] = {
            'session_id': session_id,
            'start_timestamp': sim_session.get('start_timestamp'),
            'end_timestamp': sim_session.get('end_timestamp'),
            'actors': [actor.get('name', 'Unknown') for actor in sim_session.get('initial_actors', [])],
            'scene_count': len(sim_session.get('scenes', [])),
            'total_exchanges': sim_session.get('session_statistics', {}).get('total_exchanges', 0),
            'status': 'completed' if sim_session.get('end_timestamp') else 'active',
            'file_size': self._get_session_file_size(session_id),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def list_sessions_from_index(self) -> List[Dict[str, Any]]:
        """Fast session listing using the index."""
        if not self.index_file.exists():
            return []
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            sessions = list(index.values())
            sessions.sort(key=lambda x: x.get('start_timestamp', ''), reverse=True)
            return sessions
        except:
            return []
    
    def archive_old_sessions(self, days_old: int = 30):
        """Archive sessions older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        index = {}
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        
        archived_count = 0
        for session_id, metadata in index.items():
            try:
                start_time = datetime.fromisoformat(metadata.get('start_timestamp', ''))
                if start_time < cutoff_date and metadata.get('status') == 'completed':
                    self._archive_session(session_id)
                    archived_count += 1
            except:
                continue
        
        print(f"Archived {archived_count} old sessions")
    
    def _archive_session(self, session_id: str):
        """Move a session to the archive directory."""
        for extension in ['.json', '.json.gz']:
            source_file = self.sessions_directory / f"session_{session_id}{extension}"
            if source_file.exists():
                dest_file = self.archive_directory / f"session_{session_id}{extension}"
                shutil.move(str(source_file), str(dest_file))
                break
    
    def _get_session_file_size(self, session_id: str) -> int:
        """Get the file size of a session in bytes."""
        for extension in ['.json.gz', '.json']:
            session_file = self.sessions_directory / f"session_{session_id}{extension}"
            if session_file.exists():
                return session_file.stat().st_size
        return 0
    
    def cleanup_corrupted_sessions(self):
        """Remove corrupted session files that can't be loaded."""
        corrupted = []
        
        for session_file in self.sessions_directory.glob("session_*.json*"):
            session_id = session_file.stem.replace('session_', '').replace('.json', '')
            if not self.load_session(session_id):
                corrupted.append(session_file)
        
        for file in corrupted:
            print(f"Removing corrupted session file: {file}")
            file.unlink()
        
        return len(corrupted)


class StorageRecommendations:
    """Provides storage strategy recommendations based on usage patterns."""
    
    @staticmethod
    def get_storage_strategy(session_count: int, avg_session_size_mb: float, 
                           usage_frequency: str) -> Dict[str, Any]:
        """
        Recommend storage strategy based on usage patterns.
        
        Args:
            session_count: Number of sessions
            avg_session_size_mb: Average session size in MB
            usage_frequency: 'low', 'medium', 'high'
        
        Returns:
            Dictionary with storage recommendations
        """
        recommendations = {
            'storage_type': 'json_files',
            'compression': False,
            'indexing': False,
            'archival': False,
            'database': False
        }
        
        if avg_session_size_mb > 0.1:
            recommendations['compression'] = True
        
        if session_count > 10:
            recommendations['indexing'] = True
        
        if usage_frequency == 'high' and session_count > 50:
            recommendations['archival'] = True
        
        if session_count > 500 or usage_frequency == 'high':
            recommendations['database_consideration'] = True
            recommendations['note'] = "Consider SQLite for better performance"
        
        return recommendations


UTAS_STORAGE_CONFIG = {
    'small_scale': {
        'sessions': '<50',
        'size': '<1MB each',
        'strategy': 'Simple JSON files',
        'features': ['Basic JSON storage', 'Manual cleanup']
    },
    'medium_scale': {
        'sessions': '50-200',
        'size': '1-5MB each', 
        'strategy': 'Enhanced JSON with indexing',
        'features': ['JSON with compression', 'Session index', 'Auto-archival']
    },
    'large_scale': {
        'sessions': '>200',
        'size': '>5MB each',
        'strategy': 'Consider SQLite database',
        'features': ['SQLite database', 'Full-text search', 'Advanced queries']
    }
}
