#!/usr/bin/env python3
"""Sleep pattern analysis and visualization."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def load_data(data_file: str = "raw_data.json") -> pd.DataFrame:
    """Load and preprocess raw diary data."""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S')
    return df.sort_values('date')


def parse_time(time_str):
    """Parse time string in HHMM format to time object."""
    if pd.isna(time_str) or time_str == '':
        return None
    try:
        return datetime.strptime(str(time_str).zfill(4), '%H%M').time()
    except ValueError:
        return None


def calc_sleep_duration(bedtime, wake_time):
    """Calculate sleep duration handling overnight sleep."""
    if pd.isna(bedtime) or pd.isna(wake_time):
        return None
    
    bed_dt = datetime.combine(datetime.today(), bedtime)
    wake_dt = datetime.combine(datetime.today(), wake_time)
    
    # If bedtime is after 18:00, assume it's previous day
    if bedtime.hour >= 18:
        bed_dt -= timedelta(days=1)
    
    duration = wake_dt - bed_dt
    return duration.total_seconds() / 3600  # Convert to hours


def analyze_sleep(df: pd.DataFrame) -> pd.DataFrame:
    """Process sleep-related data."""
    # Parse sleep times
    df['bedtime'] = df['昨晚實際入睡時間'].apply(parse_time)
    df['wake_time'] = df['今天實際起床時間'].apply(parse_time)
    
    # Calculate sleep duration
    df['sleep_duration'] = df.apply(
        lambda row: calc_sleep_duration(row['bedtime'], row['wake_time']), axis=1
    )
    
    # Parse other health metrics
    df['sleep_quality'] = pd.to_numeric(df['昨晚睡眠品質如何？'], errors='coerce')
    df['mood'] = pd.to_numeric(df['今日整體心情感受'], errors='coerce')
    df['energy'] = pd.to_numeric(df['今日整體精力水平如何？'], errors='coerce')
    
    return df


def plot_sleep_trends(df: pd.DataFrame):
    """Plot sleep duration trends over time."""
    plt.figure(figsize=(12, 6))
    
    # Filter out invalid data
    valid_data = df[df['sleep_duration'].notna()]
    
    plt.plot(valid_data['date'], valid_data['sleep_duration'], 
             marker='o', linewidth=2, markersize=4)
    plt.axhline(y=8, color='g', linestyle='--', alpha=0.7, label='Recommended 8h')
    plt.axhline(y=7, color='orange', linestyle='--', alpha=0.7, label='Minimum 7h')
    
    plt.title('Sleep Duration Trends Over Time', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Sleep Duration (Hours)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('sleep_duration_trends.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_sleep_quality_correlation(df: pd.DataFrame):
    """Plot correlation between sleep duration and quality."""
    plt.figure(figsize=(10, 6))
    
    # Filter valid data
    valid_data = df[(df['sleep_duration'].notna()) & (df['sleep_quality'].notna())]
    
    if len(valid_data) > 0:
        sns.scatterplot(data=valid_data, x='sleep_duration', y='sleep_quality', 
                       size='energy', sizes=(50, 200), alpha=0.7)
        plt.title('Sleep Duration vs Quality (Size = Energy Level)')
        plt.xlabel('Sleep Duration (Hours)')
        plt.ylabel('Sleep Quality (1-10)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('sleep_quality_correlation.png', dpi=300, bbox_inches='tight')
        plt.show()
    else:
        print("No valid sleep data found for correlation analysis")


def print_sleep_stats(df: pd.DataFrame):
    """Print sleep statistics summary."""
    valid_data = df[df['sleep_duration'].notna()]
    
    if len(valid_data) > 0:
        print("\nSleep Statistics Summary:")
        print(f"Average sleep duration: {valid_data['sleep_duration'].mean():.2f} hours")
        print(f"Median sleep duration: {valid_data['sleep_duration'].median():.2f} hours")
        print(f"Min sleep duration: {valid_data['sleep_duration'].min():.2f} hours")
        print(f"Max sleep duration: {valid_data['sleep_duration'].max():.2f} hours")
        print(f"Total nights tracked: {len(valid_data)}")
        
        # Sleep quality stats
        quality_data = valid_data[valid_data['sleep_quality'].notna()]
        if len(quality_data) > 0:
            print(f"Average sleep quality: {quality_data['sleep_quality'].mean():.2f}/10")
    else:
        print("No valid sleep data found")


def main():
    """Main analysis function."""
    if not Path("raw_data.json").exists():
        print("Error: raw_data.json not found. Run download_data.py first.")
        return
    
    print("Loading and analyzing sleep data...")
    
    # Load and process data
    df = load_data()
    df = analyze_sleep(df)
    
    # Generate visualizations
    plot_sleep_trends(df)
    plot_sleep_quality_correlation(df)
    
    # Print summary statistics
    print_sleep_stats(df)
    
    print("\nAnalysis complete! Check the generated PNG files.")


if __name__ == "__main__":
    main()