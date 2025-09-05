# Database creation and migration

from sqlalchemy import text
from db import engine, Base
from models import *  # Import all models
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_and_tables():
    """
    Create all database tables and set up initial configurations
    """
    try:
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Set up PostgreSQL-specific configurations
        with engine.connect() as conn:
            # Ensure UTC timezone handling
            conn.execute(text("SET timezone = 'UTC'"))
            
            # Create indexes for better performance (if not auto-created)
            logger.info("Setting up additional database optimizations...")
            
            # Commit the transaction
            conn.commit()
            
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise

def create_sample_data():
    """
    Create some sample data for testing (optional)
    """
    from sqlalchemy.orm import sessionmaker
    from werkzeug.security import generate_password_hash
    import random
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if we already have users
        if session.query(User).count() > 0:
            logger.info("Sample data already exists, skipping...")
            return
        
        # Create sample users
        sample_users = [
            {
                "name": "Test Student 1",
                "email": "test1@college.edu",
                "password_hash": generate_password_hash("testpass123"),
                "anonymous_username": f"anonymous_owl_{random.randint(1000, 9999)}",
                "college_id": "college_001",
                "college_name": "Sample University"
            },
            {
                "name": "Test Student 2", 
                "email": "test2@college.edu",
                "password_hash": generate_password_hash("testpass123"),
                "anonymous_username": f"anonymous_bear_{random.randint(1000, 9999)}",
                "college_id": "college_001",
                "college_name": "Sample University"
            }
        ]
        
        for user_data in sample_users:
            user = User(**user_data)
            session.add(user)
        
        session.commit()
        logger.info("Sample data created successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample data: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_database_and_tables()
    
    # Uncomment to create sample data
    # create_sample_data()
