# Add trend line analysis to visualize what cars are doing near signs
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
%matplotlib inline

# Assuming we already have the variables from the previous code
# This is the code to add trend line analysis

# Create a figure for trend line analysis
fig, axs = plt.subplots(2, 1, figsize=(14, 12))

# === Speed Trend Analysis ===
ax1 = axs[0]
ax1.set_title('Speed Trend Analysis Near Sign', fontsize=14)
ax1.set_xlabel('Distance from Sign (meters)', fontsize=12)
ax1.set_ylabel('Speed (km/h)', fontsize=12)

# For storing aggregated data
all_distances = []
all_speeds = []
all_headings = []

# Define the distance range around the sign to analyze
max_distance = 50  # meters

# Process data for each sign
if len(motorway_signs_db) > 0:
    for idx, sign in motorway_signs_db.iterrows():
        sign_point = sign.geometry
        
        # Create a dictionary to store all data points by distance
        distance_data = {'distance': [], 'speed': [], 'heading': []}
        
        # Collect data from all vehicles
        for trace_id, trace_df in probes_near_validation.groupby('traceid'):
            if len(trace_df) >= 3:  # Ensure enough points for meaningful data
                # Calculate distance from sign for each point
                trace_df['dist_to_sign'] = trace_df.geometry.apply(
                    lambda p: p.distance(sign_point) * 111000)  # Approx conversion to meters
                
                # Filter points within our analysis range
                trace_df = trace_df[trace_df['dist_to_sign'] <= max_distance]
                
                if len(trace_df) >= 2:  # Need at least 2 points
                    # Sort by distance to sign
                    trace_df = trace_df.sort_values('dist_to_sign')
                    
                    # Store the data
                    distance_data['distance'].extend(trace_df['dist_to_sign'].tolist())
                    distance_data['speed'].extend(trace_df['speed'].tolist())
                    distance_data['heading'].extend(trace_df['heading'].tolist())
                    
                    # Plot individual vehicle data as light scatter points
                    ax1.scatter(trace_df['dist_to_sign'], trace_df['speed'], 
                               alpha=0.3, s=20, color='gray')
                    
                    # Draw line for this vehicle
                    ax1.plot(trace_df['dist_to_sign'], trace_df['speed'], 
                            alpha=0.2, linewidth=0.5, color='gray')
        
        # Store combined data for trend analysis
        all_distances.extend(distance_data['distance'])
        all_speeds.extend(distance_data['speed'])
        all_headings.extend(distance_data['heading'])
        
        # Create bins for distance to aggregate data
        bin_width = 5  # 5-meter bins
        bins = np.arange(0, max_distance + bin_width, bin_width)
        
        binned_data = {'bin_center': [], 'avg_speed': [], 'count': []}
        
        for i in range(len(bins) - 1):
            bin_min = bins[i]
            bin_max = bins[i+1]
            bin_center = (bin_min + bin_max) / 2
            
            # Find points in this bin
            mask = (np.array(distance_data['distance']) >= bin_min) & (np.array(distance_data['distance']) < bin_max)
            speeds_in_bin = np.array(distance_data['speed'])[mask]
            
            if len(speeds_in_bin) > 0:
                avg_speed = np.mean(speeds_in_bin)
                binned_data['bin_center'].append(bin_center)
                binned_data['avg_speed'].append(avg_speed)
                binned_data['count'].append(len(speeds_in_bin))
        
        # Plot binned averages
        if binned_data['bin_center']:
            sizes = [max(20, min(200, c * 5)) for c in binned_data['count']]  # Scale point size by count
            scatter = ax1.scatter(binned_data['bin_center'], binned_data['avg_speed'], 
                      s=sizes, alpha=0.8, color='blue', edgecolor='black', zorder=5,
                      label='Binned Average')
        
        # Add trend line if we have enough data
        if len(binned_data['bin_center']) >= 3:
            # Linear regression
            X = np.array(binned_data['bin_center']).reshape(-1, 1)
            y = np.array(binned_data['avg_speed'])
            
            # Linear trend
            linear_model = LinearRegression()
            linear_model.fit(X, y)
            
            # Polynomial trend (3rd degree)
            poly_features = PolynomialFeatures(degree=3)
            X_poly = poly_features.fit_transform(X)
            poly_model = LinearRegression()
            poly_model.fit(X_poly, y)
            
            # Generate points for the trend lines
            X_plot = np.linspace(0, max_distance, 100).reshape(-1, 1)
            X_poly_plot = poly_features.transform(X_plot)
            
            # Plot trend lines
            ax1.plot(X_plot, linear_model.predict(X_plot), 
                    color='red', linestyle='--', linewidth=2, 
                    label='Linear Trend')
            
            ax1.plot(X_plot, poly_model.predict(X_poly_plot), 
                    color='green', linestyle='-', linewidth=2, 
                    label='Polynomial Trend')
            
            # Add vertical line at sign position
            ax1.axvline(x=0, color='purple', linestyle='-', linewidth=2, label='Sign Position')
            
            # Calculate slope of linear trend
            slope = linear_model.coef_[0]
            
            # Annotate with trend information
            if slope > 1:
                trend_text = f"Trend: Acceleration after sign ({slope:.2f} km/h per meter)"
            elif slope < -1:
                trend_text = f"Trend: Deceleration after sign ({slope:.2f} km/h per meter)"
            else:
                trend_text = f"Trend: Minor speed change ({slope:.2f} km/h per meter)"
            
            ax1.text(0.05, 0.95, trend_text, transform=ax1.transAxes, 
                    fontsize=12, bbox=dict(facecolor='wheat', alpha=0.5))

        
# === Heading Trend Analysis ===
ax2 = axs[1]
ax2.set_title('Heading Trend Analysis Near Sign', fontsize=14)
ax2.set_xlabel('Distance from Sign (meters)', fontsize=12)
ax2.set_ylabel('Heading (degrees)', fontsize=12)

# Process data for each sign (similar to speed analysis)
if len(motorway_signs_db) > 0:
    for idx, sign in motorway_signs_db.iterrows():
        sign_point = sign.geometry
        
        # Create a dictionary to store all data points by distance
        distance_data = {'distance': [], 'heading': []}
        
        # Collect data from all vehicles
        for trace_id, trace_df in probes_near_validation.groupby('traceid'):
            if len(trace_df) >= 3:
                # Calculate distance from sign
                trace_df['dist_to_sign'] = trace_df.geometry.apply(
                    lambda p: p.distance(sign_point) * 111000)
                
                # Filter points within our analysis range
                trace_df = trace_df[trace_df['dist_to_sign'] <= max_distance]
                
                if len(trace_df) >= 2:
                    # Sort by distance to sign
                    trace_df = trace_df.sort_values('dist_to_sign')
                    
                    # Store the data
                    distance_data['distance'].extend(trace_df['dist_to_sign'].tolist())
                    distance_data['heading'].extend(trace_df['heading'].tolist())
                    
                    # Plot individual vehicle data
                    ax2.scatter(trace_df['dist_to_sign'], trace_df['heading'], 
                               alpha=0.3, s=20, color='gray')
                    
                    # Draw line for this vehicle
                    ax2.plot(trace_df['dist_to_sign'], trace_df['heading'], 
                            alpha=0.2, linewidth=0.5, color='gray')
        
        # Create bins for distance to aggregate data
        bin_width = 5  # 5-meter bins
        bins = np.arange(0, max_distance + bin_width, bin_width)
        
        binned_data = {'bin_center': [], 'avg_heading': [], 'count': []}
        
        for i in range(len(bins) - 1):
            bin_min = bins[i]
            bin_max = bins[i+1]
            bin_center = (bin_min + bin_max) / 2
            
            # Find points in this bin
            mask = (np.array(distance_data['distance']) >= bin_min) & (np.array(distance_data['distance']) < bin_max)
            headings_in_bin = np.array(distance_data['heading'])[mask]
            
            if len(headings_in_bin) > 0:
                # For headings, we need to handle circular data properly
                # Convert to radians, calculate sin and cos components, then back to degrees
                headings_rad = np.radians(headings_in_bin)
                avg_sin = np.mean(np.sin(headings_rad))
                avg_cos = np.mean(np.cos(headings_rad))
                avg_heading = np.degrees(np.arctan2(avg_sin, avg_cos)) % 360
                
                binned_data['bin_center'].append(bin_center)
                binned_data['avg_heading'].append(avg_heading)
                binned_data['count'].append(len(headings_in_bin))
        
        # Plot binned averages
        if binned_data['bin_center']:
            sizes = [max(20, min(200, c * 5)) for c in binned_data['count']]
            ax2.scatter(binned_data['bin_center'], binned_data['avg_heading'], 
                      s=sizes, alpha=0.8, color='blue', edgecolor='black', zorder=5,
                      label='Binned Average')
        
        # For circular data like heading, polynomial fitting is not straightforward
        # Instead, we'll just connect the binned averages to show the trend
        if len(binned_data['bin_center']) >= 2:
            # Connect the binned averages with a line
            ax2.plot(binned_data['bin_center'], binned_data['avg_heading'], 
                    color='green', linestyle='-', linewidth=2, 
                    label='Heading Trend')
            
            # Add vertical line at sign position
            ax2.axvline(x=0, color='purple', linestyle='-', linewidth=2, label='Sign Position')
            
            # Calculate the average heading change
            # For this, we look at the difference between the first and last bin
            if len(binned_data['bin_center']) >= 3:
                first_heading = binned_data['avg_heading'][0]
                last_heading = binned_data['avg_heading'][-1]
                
                # Calculate the smallest angle between the two headings
                heading_diff = min((last_heading - first_heading) % 360, 
                                   (first_heading - last_heading) % 360)
                
                if heading_diff > 10:
                    trend_text = f"Significant heading change: {heading_diff:.1f}°"
                else:
                    trend_text = f"Minor heading change: {heading_diff:.1f}°"
                
                ax2.text(0.05, 0.95, trend_text, transform=ax2.transAxes, 
                        fontsize=12, bbox=dict(facecolor='wheat', alpha=0.5))

# Add legends
handles, labels = ax1.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax1.legend(by_label.values(), by_label.keys(), loc='best')

handles, labels = ax2.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax2.legend(by_label.values(), by_label.keys(), loc='best')

# Add an overall interpretation based on both trends
interpretation = ""
if len(motorway_signs_db) > 0 and 'slope' in locals():
    if abs(slope) > 1 or ('heading_diff' in locals() and heading_diff > 10):
        interpretation = "INTERPRETATION: Significant vehicle behavior changes detected near sign position.\nThis suggests the sign likely EXISTS in reality."
    else:
        interpretation = "INTERPRETATION: Minimal vehicle behavior changes detected near sign position.\nThis suggests the sign may NOT EXIST in reality."
else:
    interpretation = "INTERPRETATION: Insufficient data to determine sign existence."

fig.text(0.5, 0.01, interpretation, ha='center', fontsize=14, 
        bbox=dict(facecolor='lightyellow', alpha=0.8))

plt.tight_layout(rect=[0, 0.05, 1, 0.98])
plt.show()
