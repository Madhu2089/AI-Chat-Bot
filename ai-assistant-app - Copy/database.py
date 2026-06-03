import sqlite3
import json
import datetime
import os
import uuid

class Database:
    def __init__(self, db_path="app_data.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.create_tables()
    
    def connect(self):
        """Connect to the SQLite database"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Return Row objects that behave like dictionaries
        conn.row_factory = sqlite3.Row
        return conn
    
    def close(self, conn):
        """Close the database connection"""
        if conn:
            conn.close()
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create conversations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # Create messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            ''')
            
            # Create files table to store processed files
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
        finally:
            self.close(conn)
    
    def get_or_create_user(self):
        """Get default user or create if doesn't exist"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            # Check for any existing user
            cursor.execute("SELECT id FROM users LIMIT 1")
            user = cursor.fetchone()
            
            if not user:
                # Create a default user
                user_id = str(uuid.uuid4())
                cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
                conn.commit()
                return user_id
            
            return user['id']
        except Exception as e:
            print(f"Error getting/creating user: {e}")
            conn.rollback()
            return None
        finally:
            self.close(conn)
    
    def save_conversation(self, conversation_id, user_id, title, messages):
        """Save a conversation and its messages"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if conversation exists
            cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing conversation
                cursor.execute("""
                UPDATE conversations 
                SET title = ?, updated_at = ? 
                WHERE id = ?
                """, (title, now, conversation_id))
            else:
                # Create new conversation
                cursor.execute("""
                INSERT INTO conversations (id, user_id, title, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, user_id, title, now, now))
            
            # Delete existing messages for this conversation
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            
            # Insert messages
            for message in messages:
                message_id = str(uuid.uuid4())
                cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, created_at) 
                VALUES (?, ?, ?, ?, ?)
                """, (message_id, conversation_id, message['role'], message['content'], now))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            conn.rollback()
            return False
        finally:
            self.close(conn)
    
    def get_all_conversations(self, user_id):
        """Get all conversations for a user"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
            """, (user_id,))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return conversations
        except Exception as e:
            print(f"Error getting conversations: {e}")
            return []
        finally:
            self.close(conn)
    
    def get_conversation(self, conversation_id):
        """Get a specific conversation with its messages"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Get conversation
            cursor.execute("""
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            WHERE id = ?
            """, (conversation_id,))
            
            conv_row = cursor.fetchone()
            if not conv_row:
                return None
            
            conversation = {
                'id': conv_row['id'],
                'title': conv_row['title'],
                'created_at': conv_row['created_at'],
                'updated_at': conv_row['updated_at'],
                'messages': []
            }
            
            # Get messages for this conversation
            cursor.execute("""
            SELECT id, role, content, created_at 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at
            """, (conversation_id,))
            
            for row in cursor.fetchall():
                conversation['messages'].append({
                    'role': row['role'],
                    'content': row['content']
                })
            
            return conversation
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
        finally:
            self.close(conn)
    
    def delete_conversation(self, conversation_id):
        """Delete a conversation and its messages"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            # Delete conversation (will cascade to messages)
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            conn.rollback()
            return False
        finally:
            self.close(conn)
    
    def save_file(self, user_id, filename, file_type, file_size, file_path):
        """Save file information"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            file_id = str(uuid.uuid4())
            
            cursor.execute("""
            INSERT INTO files (id, user_id, filename, file_type, file_size, file_path) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, user_id, filename, file_type, file_size, file_path))
            
            conn.commit()
            return file_id
        except Exception as e:
            print(f"Error saving file: {e}")
            conn.rollback()
            return None
        finally:
            self.close(conn)
    
    def get_user_files(self, user_id, file_type=None):
        """Get all files for a user, optionally filtered by type"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            if file_type:
                cursor.execute("""
                SELECT id, filename, file_type, file_size, file_path, created_at 
                FROM files 
                WHERE user_id = ? AND file_type = ?
                ORDER BY created_at DESC
                """, (user_id, file_type))
            else:
                cursor.execute("""
                SELECT id, filename, file_type, file_size, file_path, created_at 
                FROM files 
                WHERE user_id = ?
                ORDER BY created_at DESC
                """, (user_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'file_type': row['file_type'],
                    'file_size': row['file_size'],
                    'file_path': row['file_path'],
                    'created_at': row['created_at']
                })
            
            return files
        except Exception as e:
            print(f"Error getting files: {e}")
            return []
        finally:
            self.close(conn)