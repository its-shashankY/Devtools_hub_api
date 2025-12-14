# app/tasks/background.py
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.api_key import APIKey

async def reset_daily_counters():
    while True:
        try:
            db = SessionLocal()
            # Reset daily counters at midnight UTC
            now = datetime.utcnow()
            next_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            sleep_seconds = (next_reset - now).total_seconds()
            
            await asyncio.sleep(sleep_seconds)
            
            # Reset all daily counters
            db.query(APIKey).update({"requests_today": 0})
            db.commit()
            
        except Exception as e:
            print(f"Error resetting daily counters: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
        
        # Sleep until next day
        await asyncio.sleep(86400)  # 24 hours

# Start the background task when the application starts
def start_background_tasks(app):
    app.state.background_tasks = set()
    task = asyncio.create_task(reset_daily_counters())
    app.state.background_tasks.add(task)
    task.add_done_callback(app.state.background_tasks.discard)