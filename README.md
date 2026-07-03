# ECommerce-Customer-Retention-Dashboard
"An interactive e-commerce data pipeline and executive dashboard built to analyze consumer behavior, track operational churn metrics, and identify high-risk inactive users using Python, SQLite, and Streamlit."
# E-Commerce Customer Attrition & Retention System

This is an operational data pipeline and interactive analytics dashboard built to monitor and analyze customer churn for e-commerce platforms. The project connects a structured relational database with an easy-to-use web interface, helping operations managers identify inactive users and take timely action to improve customer retention.

---

## Tech Stack & Tools Used

- **Language:** Python 3.x
- **Data Handling:** Pandas & NumPy
- **Database Layer:** SQLite3 (For structured SQL queries and data storage)
- **Web Interface:** Streamlit (For rendering the interactive dashboard)

---

## Database Structure (SQL Table Details)

The system organizes customer transactional history logs into a structured database table with the following metrics:

- **Customer_ID:** Unique ID for every registered customer account.
- **Signup_Month:** The month the customer created their account (e.g., January, March).
- **Region:** Geographical zone of the user (North, South, East, West).
- **Device_Type:** The platform used for shopping (Mobile or Desktop).
- **Days_Since_Last_Purchase:** Number of days since the customer last placed an order.
- **Total_Purchases:** Total number of orders placed by the customer so far.
- **Churn_Status:** Binary flag where `1` means the customer has dropped out (inactive), and `0` means they are active.

---

## How the Dashboard Works (Key Features)

### 1. Interactive Sidebar Filters
Managers can filter the entire screen's data based on **Region** and **Device Type** using simple dropdown menus. The metrics update instantly in the background without needing to refresh the browser page.

### 2. High-Level Performance Cards
The top section displays 3 quick metrics:
- **Total Monitored Customers:** Total number of customer records being scanned.
- **Average Days Since Last Purchase:** Overall platform inactivity tracker.
- **Current Churn Rate (%):** Percentage of users who have stopped using the platform.

### 3. Customer Engagement Analysis Chart
A clean visual chart that breaks down total consumer purchases across different signup cohorts, making it easy to identify monthly behavioral trends and drops in engagement.

### 4. High-Risk Retention Zone
The bottom table automatically lists all customers who have not made a single purchase in over **45 days**. Operations teams can view this list and export it to run targeted email or notification campaigns with special offers to win them back.

---

## 🚀 How to Run this Project Locally

1. Make sure you have python installed along with the required libraries:
   ```bash
   pip install streamlit pandas matplotlib
