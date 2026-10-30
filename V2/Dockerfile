FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app --home /home/app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

RUN chmod +x start.sh run.sh

USER app

ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD ["./start.sh"]
