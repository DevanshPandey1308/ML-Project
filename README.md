🎓 Student Performance Prediction

An end-to-end Machine Learning project that predicts a student's Math Score based on demographic and academic attributes. The project follows a production-style modular pipeline architecture and is deployed on AWS Elastic Beanstalk.


🚀 Key Features


End-to-End ML Pipeline (Data → Model → Deployment)
Modular, scalable project architecture
Automated Data Ingestion pipeline
Configurable Data Transformation pipeline (encoding, scaling, imputation)
Training and evaluation across multiple regression models
Automatic Best Model Selection based on evaluation metrics
Reusable Prediction Pipeline for inference
Flask-based web application for real-time predictions
Deployed on AWS Elastic Beanstalk



🛠️ Tech Stack

CategoryToolsLanguagePythonData HandlingPandas, NumPyModelingScikit-Learn, XGBoost, CatBoostWeb FrameworkFlaskDeploymentAWS Elastic BeanstalkVersion ControlGit, GitHub


🏗️ Project Architecture / Workflow

Dataset → Data Ingestion → Data Transformation → Model Training → 
Model Evaluation → Best Model Selection → Model Serialization → 
Prediction Pipeline → Flask Application → AWS Deployment

Models Evaluated


Linear Regression
Decision Tree Regressor
Random Forest Regressor
Gradient Boosting Regressor
AdaBoost Regressor
XGBoost Regressor
CatBoost Regressor


The best-performing model is automatically selected based on evaluation metrics and serialized for use in the prediction pipeline.


📁 Project Structure

ML_Project
├── artifacts                  # Stored datasets, models, and preprocessor objects
├── src
│   ├── components             # Data ingestion, transformation, model training
│   ├── pipeline                # Training and prediction pipelines
│   ├── logger.py              # Logging configuration
│   ├── exception.py           # Custom exception handling
│   └── utils.py               # Common utility functions
├── templates                  # HTML templates for Flask app
├── static                      # Static assets (CSS, JS, images)
├── application.py             # Flask application entry point
├── requirements.txt           # Project dependencies
├── setup.py                    # Package setup configuration
└── README.md


⚙️ Installation & Setup

bash# Clone the repository
git clone https://github.com/<your-username>/student-performance-prediction.git
cd student-performance-prediction

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask application
python application.py

The app will be available at http://127.0.0.1:5000/


📸 Screenshots

Home PagePrediction Result[Add screenshot here][Add screenshot here]


🔮 Future Improvements


Add CI/CD pipeline using GitHub Actions
Containerize the application using Docker
Integrate MLflow for experiment tracking
Add hyperparameter tuning with Optuna
Build a REST API layer for programmatic predictions
Add unit tests and test coverage reports



👤 Author

Devansh Pandey
Data Science Enthusiast
Email: devanshp171@gmail.com
