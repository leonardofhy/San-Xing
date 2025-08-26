#!/usr/bin/env python3
"""
Generate sample data for San-Xing dashboard testing.
This creates a JSON file with sample diary entries to test the dashboard.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_data(num_days: int = 30) -> list:
    """Generate sample diary data for testing."""
    activities_pool = [
        "英文學習", "閱讀論文", "看書", "戶外活動", "實體社交活動",
        "看知識型視頻", "看英文視頻", "做家務", "頭髮護理", "面部護理",
        "打遊戲", "滑手機", "看娛樂視頻", "額外完成一個任務"
    ]
    
    data = []
    base_date = datetime.now() - timedelta(days=num_days)
    
    for i in range(num_days):
        date = base_date + timedelta(days=i)
        
        # Generate random activities (2-5 activities per day)
        num_activities = random.randint(2, 5)
        selected_activities = random.sample(activities_pool, num_activities)
        activities_str = ", ".join(selected_activities)
        
        # Generate realistic time values
        bedtime_hour = random.randint(22, 25) % 24  # 22:00-01:00
        bedtime_min = random.choice([0, 15, 30, 45])
        bedtime = f"{bedtime_hour:02d}{bedtime_min:02d}"
        
        wake_hour = random.randint(6, 9)  # 06:00-09:00
        wake_min = random.choice([0, 15, 30, 45])
        wake_time = f"{wake_hour:02d}{wake_min:02d}"
        
        entry = {
            "Timestamp": date.strftime("%d/%m/%Y %H:%M:%S"),
            "今日整體心情感受": random.randint(4, 10),  # Mood 4-10
            "今日整體精力水平如何？": random.randint(3, 9),  # Energy 3-9
            "昨晚睡眠品質如何？": random.randint(4, 9),  # Sleep quality 4-9
            "昨晚實際入睡時間": bedtime,
            "今天實際起床時間": wake_time,
            "體重紀錄": round(random.uniform(60.0, 80.0), 1),  # Weight 60-80kg
            "今日手機螢幕使用時間": round(random.uniform(2.0, 8.0), 1),  # Screen time 2-8 hours
            "今天完成了哪些？": activities_str,
            "今日日記": f"Sample diary entry for {date.strftime('%Y-%m-%d')}. " +
                       f"Today was a {'good' if random.random() > 0.3 else 'challenging'} day. " +
                       f"I focused on {random.choice(['work', 'learning', 'health', 'relationships'])}."
        }
        data.append(entry)
    
    return data


def main():
    """Generate and save sample data."""
    print("Generating sample San-Xing data...")
    
    # Generate 30 days of sample data
    sample_data = generate_sample_data(30)
    
    # Save to JSON file
    output_path = Path(__file__).parent / "raw_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(sample_data)} sample entries")
    print(f"Saved to: {output_path}")
    print(f"Now run: uv run python run_dashboard.py")


if __name__ == "__main__":
    main()