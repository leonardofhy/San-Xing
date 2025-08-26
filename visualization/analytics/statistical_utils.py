"""Statistical Utilities for San-Xing Dashboard.

This module provides statistical functions for significance testing,
confidence intervals, and correlation analysis with proper statistical rigor.
"""

from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
import warnings


def calculate_significance(x: pd.Series, y: pd.Series, test_type: str = 'correlation') -> Dict[str, Any]:
    """Calculate statistical significance between two variables.
    
    Args:
        x: First variable series
        y: Second variable series
        test_type: Type of test ('correlation', 't_test', 'mann_whitney')
        
    Returns:
        dict: {
            'p_value': float,
            'effect_size': float,
            'confidence_interval': tuple,
            'test_statistic': float,
            'significant': bool (at alpha=0.05)
        }
    """
    # Remove NaN values
    clean_data = pd.DataFrame({'x': x, 'y': y}).dropna()
    
    if len(clean_data) < 3:
        return {
            'p_value': 1.0,
            'effect_size': 0.0,
            'confidence_interval': (0.0, 0.0),
            'test_statistic': 0.0,
            'significant': False,
            'sample_size': len(clean_data),
            'test_type': test_type
        }
    
    x_clean = clean_data['x']
    y_clean = clean_data['y']
    
    if test_type == 'correlation':
        # Pearson correlation test
        corr, p_value = stats.pearsonr(x_clean, y_clean)
        
        # Effect size is the correlation coefficient itself
        effect_size = abs(corr)
        
        # Confidence interval for correlation
        n = len(x_clean)
        if n > 3:
            z_score = 0.5 * np.log((1 + corr) / (1 - corr))
            se = 1 / np.sqrt(n - 3)
            z_critical = stats.norm.ppf(0.975)  # 95% CI
            
            lower_z = z_score - z_critical * se
            upper_z = z_score + z_critical * se
            
            lower_r = (np.exp(2 * lower_z) - 1) / (np.exp(2 * lower_z) + 1)
            upper_r = (np.exp(2 * upper_z) - 1) / (np.exp(2 * upper_z) + 1)
            
            confidence_interval = (lower_r, upper_r)
        else:
            confidence_interval = (-1.0, 1.0)
        
        test_statistic = corr
        
    elif test_type == 't_test':
        # Independent t-test
        statistic, p_value = stats.ttest_ind(x_clean, y_clean, equal_var=False)
        
        # Cohen's d effect size
        pooled_std = np.sqrt(((len(x_clean) - 1) * x_clean.var() + 
                             (len(y_clean) - 1) * y_clean.var()) / 
                            (len(x_clean) + len(y_clean) - 2))
        
        if pooled_std > 0:
            effect_size = abs(x_clean.mean() - y_clean.mean()) / pooled_std
        else:
            effect_size = 0.0
        
        # Rough CI for Cohen's d (simplified)
        confidence_interval = (max(0, effect_size - 0.5), effect_size + 0.5)
        test_statistic = statistic
        
    elif test_type == 'mann_whitney':
        # Mann-Whitney U test (non-parametric)
        statistic, p_value = stats.mannwhitneyu(x_clean, y_clean, alternative='two-sided')
        
        # Effect size r = Z / sqrt(N)
        n_total = len(x_clean) + len(y_clean)
        z_score = abs(stats.norm.ppf(p_value / 2))
        effect_size = z_score / np.sqrt(n_total) if n_total > 0 else 0.0
        
        confidence_interval = (max(0, effect_size - 0.2), min(1, effect_size + 0.2))
        test_statistic = statistic
    
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    return {
        'p_value': float(p_value),
        'effect_size': float(effect_size),
        'confidence_interval': tuple(map(float, confidence_interval)),
        'test_statistic': float(test_statistic),
        'significant': p_value < 0.05,
        'sample_size': len(clean_data),
        'test_type': test_type
    }


def minimum_sample_size_check(df: pd.DataFrame, analysis_type: str = 'correlation') -> Dict[str, Any]:
    """Check if DataFrame has sufficient sample size for analysis.
    
    Args:
        df: Input DataFrame
        analysis_type: Type of statistical analysis
        
    Returns:
        dict: {
            'sufficient': bool,
            'actual_size': int,
            'required_size': int,
            'confidence_level': str
        }
    """
    min_sizes = {
        'correlation': 10,    # Minimum for meaningful correlation
        'trend': 14,         # 2 weeks for trend analysis
        'kpi': 7,           # 1 week for KPI calculation
        't_test': 30,        # Rule of thumb for t-test normality
        'regression': 20,    # Basic multiple regression
        'anova': 15          # One-way ANOVA
    }
    
    required_size = min_sizes.get(analysis_type, 10)
    actual_size = len(df)
    sufficient = actual_size >= required_size
    
    # Determine confidence level based on sample size
    if actual_size < required_size:
        confidence_level = 'low'
    elif actual_size < required_size * 2:
        confidence_level = 'medium'
    else:
        confidence_level = 'high'
    
    return {
        'sufficient': sufficient,
        'actual_size': actual_size,
        'required_size': required_size,
        'confidence_level': confidence_level,
        'analysis_type': analysis_type
    }


def correlation_with_significance(df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate correlations with significance testing and multiple comparison correction.
    
    Args:
        df: Input DataFrame with numeric columns
        alpha: Significance level
        
    Returns:
        dict: {
            'significant_correlations': list of significant pairs,
            'all_correlations': dict of all correlation results,
            'total_tests': int,
            'alpha_level': float,
            'corrected_alpha': float (Bonferroni)
        }
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        return {
            'significant_correlations': [],
            'all_correlations': {},
            'total_tests': 0,
            'alpha_level': alpha,
            'corrected_alpha': alpha
        }
    
    total_tests = len(numeric_cols) * (len(numeric_cols) - 1) // 2
    corrected_alpha = alpha / total_tests if total_tests > 1 else alpha  # Bonferroni correction
    
    significant_correlations = []
    all_correlations = {}
    
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols[i + 1:], i + 1):
            series1 = df[col1].dropna()
            series2 = df[col2].dropna()
            
            # Align series by index
            common_idx = series1.index.intersection(series2.index)
            if len(common_idx) < 3:
                continue
            
            aligned1 = series1.loc[common_idx]
            aligned2 = series2.loc[common_idx]
            
            # Calculate correlation significance
            result = calculate_significance(aligned1, aligned2, test_type='correlation')
            
            pair_key = f"{col1}_vs_{col2}"
            all_correlations[pair_key] = result
            
            # Check significance with corrected alpha
            if result['p_value'] < corrected_alpha:
                significant_correlations.append({
                    'variable_1': col1,
                    'variable_2': col2,
                    'correlation': result['test_statistic'],
                    'p_value': result['p_value'],
                    'effect_size': result['effect_size'],
                    'sample_size': result['sample_size']
                })
    
    return {
        'significant_correlations': significant_correlations,
        'all_correlations': all_correlations,
        'total_tests': total_tests,
        'alpha_level': alpha,
        'corrected_alpha': corrected_alpha
    }


def trend_significance(series: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """Test statistical significance of trend in time series using Mann-Kendall test.
    
    Args:
        series: Time series data
        alpha: Significance level
        
    Returns:
        dict: {
            'trend_direction': str,
            'p_value': float,
            'tau': float (Kendall's tau),
            'z_score': float,
            'significant': bool
        }
    """
    # Remove NaN values
    data = series.dropna()
    n = len(data)
    
    if n < 3:
        return {
            'trend_direction': 'stable',
            'p_value': 1.0,
            'tau': 0.0,
            'z_score': 0.0,
            'significant': False,
            'sample_size': n
        }
    
    # Mann-Kendall test implementation
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            if data.iloc[j] > data.iloc[i]:
                s += 1
            elif data.iloc[j] < data.iloc[i]:
                s -= 1
    
    # Calculate variance
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Handle ties (simplified - could be more sophisticated)
    unique_vals = data.nunique()
    if unique_vals < n:
        # Rough correction for ties
        tie_correction = (n - unique_vals) * 2
        var_s -= tie_correction
    
    var_s = max(var_s, 1)  # Prevent division by zero
    
    # Calculate Z-score
    if s > 0:
        z_score = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z_score = (s + 1) / np.sqrt(var_s)
    else:
        z_score = 0.0
    
    # Calculate p-value (two-tailed)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # Calculate Kendall's tau
    tau = s / (n * (n - 1) / 2)
    
    # Determine trend direction
    if p_value < alpha:
        if s > 0:
            trend_direction = 'improving'
        else:
            trend_direction = 'declining'
    else:
        trend_direction = 'stable'
    
    return {
        'trend_direction': trend_direction,
        'p_value': float(p_value),
        'tau': float(tau),
        'z_score': float(z_score),
        'significant': p_value < alpha,
        'sample_size': n,
        'mann_kendall_s': int(s)
    }


def calculate_confidence_interval(data: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for mean.
    
    Args:
        data: Data series
        confidence: Confidence level (0-1)
        
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    clean_data = data.dropna()
    n = len(clean_data)
    
    if n < 2:
        mean_val = clean_data.mean() if n > 0 else 0.0
        return (mean_val, mean_val)
    
    mean = clean_data.mean()
    sem = stats.sem(clean_data)  # Standard error of mean
    
    # Use t-distribution for small samples
    if n < 30:
        t_critical = stats.t.ppf((1 + confidence) / 2, df=n - 1)
        margin_error = t_critical * sem
    else:
        z_critical = stats.norm.ppf((1 + confidence) / 2)
        margin_error = z_critical * sem
    
    return (mean - margin_error, mean + margin_error)


def effect_size_interpretation(effect_size: float, test_type: str = 'correlation') -> str:
    """Interpret effect size magnitude according to Cohen's conventions.
    
    Args:
        effect_size: Calculated effect size
        test_type: Type of test ('correlation', 'd', 'eta_squared')
        
    Returns:
        str: Interpretation ('small', 'medium', 'large')
    """
    if test_type == 'correlation':
        # Cohen's conventions for correlation
        if abs(effect_size) < 0.1:
            return 'negligible'
        elif abs(effect_size) < 0.3:
            return 'small'
        elif abs(effect_size) < 0.5:
            return 'medium'
        else:
            return 'large'
    
    elif test_type == 'd':
        # Cohen's d conventions
        if abs(effect_size) < 0.2:
            return 'negligible'
        elif abs(effect_size) < 0.5:
            return 'small'
        elif abs(effect_size) < 0.8:
            return 'medium'
        else:
            return 'large'
    
    else:
        # Generic interpretation
        if abs(effect_size) < 0.2:
            return 'small'
        elif abs(effect_size) < 0.5:
            return 'medium'
        else:
            return 'large'