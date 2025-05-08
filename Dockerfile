# Use the official Python runtime as a base image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app's code into the container
COPY . .

# Expose the port your app runs on (default Flask port is 5000)
EXPOSE 5000

# Command to run your app (e.g., Flask app: `python app.py`)
CMD ["python", "app.py"]
