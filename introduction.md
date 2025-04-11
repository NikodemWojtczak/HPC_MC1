# WebScale Retail: Real-Time Data Processing Solution

## Client Profile
**WebScale Retail** is a large online e-commerce platform operator requiring integrated processing of customer interaction data and critical infrastructure monitoring.

## Initial Situation & Data

### Data Sources
1. **User Activity Topic**
   - Source: Web application servers
   - Content: User interactions (page views, button clicks, cart additions, purchases, logouts)
   - Purpose: Real-time insights and analytics

2. **Sensor Data Topic**
   - Source: Environmental sensors in data centers
   - Content: Server rack temperature and humidity measurements
   - Purpose: Ensuring optimal operating conditions

### Current Limitations
These data streams are currently logged separately, making real-time correlation and unified analysis challenging.

## Problem Statement

WebScale Retail faces three key challenges:
1. **Infrastructure Monitoring**: Requirement for real-time monitoring of data center conditions with alerts for abnormal values
2. **Data Integration**: Need for a unified system to ingest, process, and store both data types for comprehensive operational monitoring and business intelligence

## Proposed Solution (Kafka Implementation)

### Pipeline Components
1. **Data Ingestion**
   - Implement Kafka streaming pipeline to capture both user_activity events and sensor_data readings in real-time

2. **Stream Processing**
   - Enrich sensor data with status classifications (Normal, Warning, Low)
   - Aggregate user actions and identify key events from the activity stream

3. **Data Destinations**
   - Persistent data store (CSV files) for historical analysis of user trends and infrastructure health
