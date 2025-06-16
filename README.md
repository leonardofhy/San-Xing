# Meta-Awareness System

This is a personalized Meta-Awareness automation system built on **Google Apps Script**. Its goal is to establish an effective, personalized feedback loop for personal growth.

The core function of this project is to automatically generate a daily report by integrating and quantifying personal daily data (such as behaviors, sleep patterns, etc.) and leveraging AI to provide insightful feedback.

## ✨ Core Features

  - **Automated Daily Reports**: A time-driven trigger automatically generates a qualitative report featuring feedback from an AI coach.
  - **AI-Powered In-depth Analysis**: Integrates with the DeepSeek API to transform your log data into structured insights and recommendations.
  - **Quantitative Behavior Scoring**: Converts your daily activities into a trackable "Daily Efficiency Score."
  - **Sleep Quality Analysis**: Provides a comprehensive assessment of your sleep health across multiple dimensions.
  - **Automated Email Delivery**: Automatically sends a formatted HTML report to your specified email address each day.

## ⚠️ Important Notices & Privacy Disclaimer

1.  **Data Transmission**: To generate AI-powered analysis, this script collects your personal data recorded in your Google Sheet (including but not limited to your behaviors, sleep patterns, mood, weight, and free-form notes) and sends this data via an API to a **third-party Large Language Model (LLM) service provider (currently DeepSeek)**.
2.  **Third-Party Policies**: You are responsible for reviewing and understanding the data privacy policies of the third-party service provider. The author of this project is not liable for how your data is used or stored by the third-party service.
3.  **Assumption of Risk**: By using this system, you understand and agree to the potential privacy risks associated with transmitting sensitive personal data to a third-party service. Please use the core AI analysis features only after a thorough personal risk assessment.

## 🌐 Language Support Note

Currently, the AI prompts used in this system are in Traditional Chinese. We plan to modularize the API interface in the future to support multiple languages and make it easier for users to customize prompts in their preferred language.

## 🚀 Deployment & Configuration Guide

This guide is primarily intended for developers or users with a basic understanding of Google Apps Script.

### 1\. Deploy Project Files

Use the [Google Apps Script CLI (clasp)](https://github.com/google/clasp) or manually copy and paste the contents of the `.js` files from this repository into your Google Apps Script project.

### 2\. Configure Script Properties (Required)

Navigate to "Project Settings" ⚙️ \> "Script Properties" and add the following two properties:

  - `DEEPSEEK_API_KEY`: Your DeepSeek API Key.
  - `RECIPIENT_EMAIL`: The email address where you want to receive reports.

### 3\. Customize `Config.js`

Open the `Config.js` file to adjust non-sensitive parameters according to your preferences, such as email subjects, model names, etc.

### 4\. Prepare the Data Source

  - This system requires a Google Sheet as its data source (default name is `MetaLog`).
  - Currently, the data extraction logic in the script (specifically the `_extractDataFromRow` function) is tailored to the developer's personal data structure. You will need to modify this function to correctly map the columns according to your own data format.
  - **Future Plans**: We plan to provide a standardized Google Form template and a corresponding setup guide in the future to make it easier for new users to get started.

### 5\. Initialization & Trigger Setup

  - **Daily Trigger**: In the "Triggers" ⏰ section, create a new daily time-based trigger to execute the `runDailyReportGeneration` function at your preferred time.

## 📄 License

This project is licensed under the [MIT License](./LICENSE).