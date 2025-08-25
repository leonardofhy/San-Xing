#!/usr/bin/env python3
"""Activity pattern analysis and mood correlation."""

import json
from pathlib import Path
from collections import Counter

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


def analyze_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Process and categorize activities."""
    # Parse mood and energy
    df['mood'] = pd.to_numeric(df['今日整體心情感受'], errors='coerce')
    df['energy'] = pd.to_numeric(df['今日整體精力水平如何？'], errors='coerce')
    
    # Define activity categories
    positive_activities = [
        '英文學習', '閱讀論文', '看書', '戶外活動', '實體社交活動', 
        '看知識型視頻', '看英文視頻', '額外完成一個任務', '額外完成兩個任務', 
        '額外完成三個或以上任務'
    ]
    
    neutral_activities = [
        '做家務', '頭髮護理', '面部護理', '久坐'
    ]
    
    negative_activities = [
        '打遊戲', '滑手機', '看娛樂視頻'
    ]
    
    # Count activities by category
    def count_activities_by_category(activities_str, category_list):
        if pd.isna(activities_str):
            return 0
        return sum(1 for activity in category_list if activity in str(activities_str))
    
    df['positive_activities'] = df['今天完成了哪些？'].apply(
        lambda x: count_activities_by_category(x, positive_activities)
    )
    df['neutral_activities'] = df['今天完成了哪些？'].apply(
        lambda x: count_activities_by_category(x, neutral_activities)
    )
    df['negative_activities'] = df['今天完成了哪些？'].apply(
        lambda x: count_activities_by_category(x, negative_activities)
    )
    
    # Calculate activity balance score
    df['activity_balance'] = df['positive_activities'] - df['negative_activities']
    
    return df


def plot_activities_vs_mood(df: pd.DataFrame):
    """Plot relationship between activities and mood."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Filter valid data
    valid_data = df[df['mood'].notna()]
    
    # Positive activities vs mood
    if len(valid_data) > 0:
        sns.boxplot(data=valid_data, x='positive_activities', y='mood', ax=axes[0])
        axes[0].set_title('Mood Distribution by Positive Activities Count')
        axes[0].set_xlabel('Number of Positive Activities')
        axes[0].set_ylabel('Mood Level (1-10)')
        axes[0].grid(True, alpha=0.3)
        
        # Negative activities vs mood
        sns.boxplot(data=valid_data, x='negative_activities', y='mood', ax=axes[1])
        axes[1].set_title('Mood Distribution by Negative Activities Count')
        axes[1].set_xlabel('Number of Negative Activities')
        axes[1].set_ylabel('Mood Level (1-10)')
        axes[1].grid(True, alpha=0.3)
        
        # Activity balance vs mood
        sns.scatterplot(data=valid_data, x='activity_balance', y='mood', 
                       size='energy', sizes=(50, 200), alpha=0.7, ax=axes[2])
        axes[2].set_title('Activity Balance vs Mood (Size = Energy)')
        axes[2].set_xlabel('Activity Balance Score')
        axes[2].set_ylabel('Mood Level (1-10)')
        axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('activities_vs_mood.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_activity_trends(df: pd.DataFrame):
    """Plot activity trends over time."""
    plt.figure(figsize=(14, 8))
    
    # Create stacked area chart
    valid_data = df[['date', 'positive_activities', 'neutral_activities', 'negative_activities']].dropna()
    
    if len(valid_data) > 0:
        plt.stackplot(valid_data['date'], 
                     valid_data['positive_activities'],
                     valid_data['neutral_activities'], 
                     valid_data['negative_activities'],
                     labels=['Positive', 'Neutral', 'Negative'],
                     colors=['green', 'gray', 'red'],
                     alpha=0.7)
        
        plt.title('Activity Types Over Time (Stacked)')
        plt.xlabel('Date')
        plt.ylabel('Number of Activities')
        plt.legend(loc='upper right')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('activity_trends.png', dpi=300, bbox_inches='tight')
        plt.show()
    else:
        print("No valid activity data found for trends")


def analyze_most_common_activities(df: pd.DataFrame):
    """Analyze and visualize most common activities."""
    all_activities = []
    
    for activities_str in df['今天完成了哪些？'].dropna():
        if activities_str and activities_str.strip():
            # Split by comma and clean up
            activities = [act.strip() for act in str(activities_str).split(',')]
            all_activities.extend(activities)
    
    if not all_activities:
        print("No activity data found")
        return
    
    # Count activities
    activity_counts = Counter(all_activities)
    
    # Get top 10 activities
    top_activities = activity_counts.most_common(10)
    
    if top_activities:
        activities, counts = zip(*top_activities)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(activities)), counts)
        plt.yticks(range(len(activities)), activities)
        plt.xlabel('Frequency')
        plt.title('Top 10 Most Common Activities')
        plt.gca().invert_yaxis()
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            plt.text(count + 0.1, i, str(count), va='center')
        
        plt.tight_layout()
        plt.savefig('top_activities.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print the results
        print("\nMost Common Activities:")
        print("=" * 30)
        for activity, count in top_activities:
            print(f"{activity}: {count} times")


def plot_weekly_activity_patterns(df: pd.DataFrame):
    """Analyze activity patterns by day of week."""
    valid_data = df[df['positive_activities'].notna()].copy()
    
    if len(valid_data) == 0:
        print("No valid activity data for weekly analysis")
        return
    
    # Add day of week
    valid_data['day_of_week'] = valid_data['date'].dt.day_name()
    valid_data['weekday_order'] = valid_data['date'].dt.dayofweek
    
    # Group by day of week
    weekly_stats = valid_data.groupby(['day_of_week', 'weekday_order']).agg({
        'positive_activities': 'mean',
        'negative_activities': 'mean',
        'mood': 'mean',
        'energy': 'mean'
    }).reset_index().sort_values('weekday_order')
    
    if len(weekly_stats) > 0:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Positive activities by day
        axes[0,0].bar(weekly_stats['day_of_week'], weekly_stats['positive_activities'], color='green', alpha=0.7)
        axes[0,0].set_title('Average Positive Activities by Day of Week')
        axes[0,0].set_ylabel('Count')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # Negative activities by day
        axes[0,1].bar(weekly_stats['day_of_week'], weekly_stats['negative_activities'], color='red', alpha=0.7)
        axes[0,1].set_title('Average Negative Activities by Day of Week')
        axes[0,1].set_ylabel('Count')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # Mood by day
        axes[1,0].bar(weekly_stats['day_of_week'], weekly_stats['mood'], color='blue', alpha=0.7)
        axes[1,0].set_title('Average Mood by Day of Week')
        axes[1,0].set_ylabel('Mood (1-10)')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # Energy by day
        axes[1,1].bar(weekly_stats['day_of_week'], weekly_stats['energy'], color='orange', alpha=0.7)
        axes[1,1].set_title('Average Energy by Day of Week')
        axes[1,1].set_ylabel('Energy (1-10)')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('weekly_patterns.png', dpi=300, bbox_inches='tight')
        plt.show()


def print_activity_stats(df: pd.DataFrame):
    """Print activity analysis statistics."""
    valid_data = df[['positive_activities', 'negative_activities', 'activity_balance', 'mood', 'energy']].dropna()
    
    if len(valid_data) > 0:
        print("\nActivity Analysis Summary:")
        print("=" * 40)
        print(f"Average positive activities per day: {valid_data['positive_activities'].mean():.2f}")
        print(f"Average negative activities per day: {valid_data['negative_activities'].mean():.2f}")
        print(f"Average activity balance score: {valid_data['activity_balance'].mean():.2f}")
        
        # Correlation with mood and energy
        pos_mood_corr = valid_data['positive_activities'].corr(valid_data['mood'])
        neg_mood_corr = valid_data['negative_activities'].corr(valid_data['mood'])
        balance_mood_corr = valid_data['activity_balance'].corr(valid_data['mood'])
        
        print(f"\nCorrelations with Mood:")
        print(f"  Positive activities: {pos_mood_corr:.3f}")
        print(f"  Negative activities: {neg_mood_corr:.3f}")
        print(f"  Activity balance: {balance_mood_corr:.3f}")
    else:
        print("No valid activity data found")


def main():
    """Main activity analysis function."""
    if not Path("raw_data.json").exists():
        print("Error: raw_data.json not found. Run download_data.py first.")
        return
    
    print("Loading and analyzing activity data...")
    
    # Load and process data
    df = load_data()
    df = analyze_activities(df)
    
    # Generate visualizations
    print("Generating activity vs mood analysis...")
    plot_activities_vs_mood(df)
    
    print("Generating activity trends...")
    plot_activity_trends(df)
    
    print("Analyzing most common activities...")
    analyze_most_common_activities(df)
    
    print("Analyzing weekly patterns...")
    plot_weekly_activity_patterns(df)
    
    # Print summary statistics
    print_activity_stats(df)
    
    print("\nActivity analysis complete! Check the generated PNG files.")


if __name__ == "__main__":
    main()