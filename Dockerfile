FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/employee_goal_tracker
COPY requirements.txt ./
RUN pip install -r requirements.txt ./
