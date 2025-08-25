#!/usr/bin/env python3
"""Comprehensive health dashboard with multiple metrics."""

import json
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


def process_health_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Process all health-related metrics."""
    # Basic health metrics
    df['mood'] = pd.to_numeric(df['今日整體心情感受'], errors='coerce')
    df['energy'] = pd.to_numeric(df['今日整體精力水平如何？'], errors='coerce')
    df['sleep_quality'] = pd.to_numeric(df['昨晚睡眠品質如何？'], errors='coerce')
    df['weight'] = pd.to_numeric(df['體重紀錄'], errors='coerce')
    df['screen_time'] = pd.to_numeric(df['今日手機螢幕使用時間'], errors='coerce')
    
    # Calculate weight moving average
    df['weight_ma'] = df['weight'].rolling(window=7, min_periods=1).mean()
    
    return df


def plot_multi_factor_dashboard(df: pd.DataFrame):
    """Create a comprehensive health dashboard."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Mood over time
    valid_mood = df[df['mood'].notna()]
    axes[0,0].plot(valid_mood['date'], valid_mood['mood'], 'g-o', alpha=0.7, markersize=3)
    axes[0,0].set_title('Daily Mood Levels')
    axes[0,0].set_ylabel('Mood (1-10)')
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # Energy over time
    valid_energy = df[df['energy'].notna()]
    axes[0,1].plot(valid_energy['date'], valid_energy['energy'], 'b-o', alpha=0.7, markersize=3)
    axes[0,1].set_title('Daily Energy Levels')
    axes[0,1].set_ylabel('Energy (1-10)')
    axes[0,1].grid(True, alpha=0.3)
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # Screen time
    valid_screen = df[df['screen_time'].notna()]
    axes[0,2].plot(valid_screen['date'], valid_screen['screen_time'], 'r-o', alpha=0.7, markersize=3)
    axes[0,2].set_title('Daily Screen Time')
    axes[0,2].set_ylabel('Hours')
    axes[0,2].grid(True, alpha=0.3)
    axes[0,2].tick_params(axis='x', rotation=45)
    
    # Weight trends with moving average
    valid_weight = df[df['weight'].notna()]
    axes[1,0].plot(valid_weight['date'], valid_weight['weight'], 'o-', alpha=0.6, 
                   markersize=3, label='Daily Weight')
    axes[1,0].plot(valid_weight['date'], valid_weight['weight_ma'], '-', 
                   linewidth=2, label='7-Day Average')
    axes[1,0].set_title('Weight Trends')
    axes[1,0].set_ylabel('Weight (kg)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # Sleep quality over time
    valid_sleep = df[df['sleep_quality'].notna()]
    axes[1,1].plot(valid_sleep['date'], valid_sleep['sleep_quality'], 'm-o', alpha=0.7, markersize=3)
    axes[1,1].set_title('Sleep Quality')
    axes[1,1].set_ylabel('Quality (1-10)')
    axes[1,1].grid(True, alpha=0.3)
    axes[1,1].tick_params(axis='x', rotation=45)
    
    # Mood vs Energy correlation
    valid_both = df[(df['mood'].notna()) & (df['energy'].notna())]
    if len(valid_both) > 0:
        axes[1,2].scatter(valid_both['mood'], valid_both['energy'], alpha=0.7)
        axes[1,2].set_title('Mood vs Energy Correlation')
        axes[1,2].set_xlabel('Mood (1-10)')
        axes[1,2].set_ylabel('Energy (1-10)')
        axes[1,2].grid(True, alpha=0.3)
        
        # Add correlation coefficient
        corr = valid_both['mood'].corr(valid_both['energy'])
        axes[1,2].text(0.05, 0.95, f'r = {corr:.3f}', transform=axes[1,2].transAxes,
                      bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('health_dashboard.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_correlation_heatmap(df: pd.DataFrame):
    """Plot correlation matrix of health metrics."""
    health_cols = ['mood', 'energy', 'sleep_quality', 'weight', 'screen_time']
    health_data = df[health_cols].dropna()
    
    if len(health_data) < 2:
        print("Insufficient data for correlation analysis")
        return
    
    plt.figure(figsize=(10, 8))
    correlation_matrix = health_data.corr()
    
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, fmt='.2f', linewidths=0.5)
    plt.title('Health Metrics Correlation Matrix')
    plt.tight_layout()
    plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_screen_time_vs_sleep(df: pd.DataFrame):
    """Analyze relationship between screen time and sleep quality."""
    valid_data = df[(df['screen_time'].notna()) & (df['sleep_quality'].notna()) & (df['mood'].notna())]
    
    if len(valid_data) == 0:
        print("No valid data for screen time vs sleep analysis")
        return
    
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(valid_data['screen_time'], valid_data['sleep_quality'], 
                         c=valid_data['mood'], cmap='viridis', s=60, alpha=0.7, 
                         edgecolors='black', linewidth=0.5)
    plt.colorbar(scatter, label='Mood Level')
    plt.xlabel('Screen Time (Hours)')
    plt.ylabel('Sleep Quality (1-10)')
    plt.title('Screen Time vs Sleep Quality (Color = Mood)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('screen_time_vs_sleep.png', dpi=300, bbox_inches='tight')
    plt.show()


def print_health_summary(df: pd.DataFrame):
    """Print comprehensive health statistics."""
    print("\nHealth Metrics Summary:")
    print("=" * 40)
    
    metrics = {
        'Mood': df['mood'],
        'Energy': df['energy'],
        'Sleep Quality': df['sleep_quality'],
        'Weight': df['weight'],
        'Screen Time': df['screen_time']
    }
    
    for name, data in metrics.items():
        valid_data = data.dropna()
        if len(valid_data) > 0:
            print(f"\n{name}:")
            print(f"  Average: {valid_data.mean():.2f}")
            print(f"  Median: {valid_data.median():.2f}")
            print(f"  Min: {valid_data.min():.2f}")
            print(f"  Max: {valid_data.max():.2f}")
            print(f"  Data points: {len(valid_data)}")
        else:
            print(f"\n{name}: No valid data found")


def main():
    """Main dashboard function."""
    if not Path("raw_data.json").exists():
        print("Error: raw_data.json not found. Run download_data.py first.")
        return
    
    print("Loading and processing health data...")
    
    # Load and process data
    df = load_data()
    df = process_health_metrics(df)
    
    # Generate visualizations
    print("Generating health dashboard...")
    plot_multi_factor_dashboard(df)
    
    print("Generating correlation heatmap...")
    plot_correlation_heatmap(df)
    
    print("Analyzing screen time vs sleep quality...")
    plot_screen_time_vs_sleep(df)
    
    # Print summary statistics
    print_health_summary(df)
    
    print("\nDashboard complete! Check the generated PNG files.")


if __name__ == "__main__":
    main()