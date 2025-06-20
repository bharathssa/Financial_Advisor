FROM python:3.9.6-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .streamlit /app/.streamlit

EXPOSE 8501

CMD ["python3", "-m", "streamlit", "run", "emily_streamlit_retirement_app.py"]

