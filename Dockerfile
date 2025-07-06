# /home/s0001666/Working_dir/my_repos/Kineto/Kineto/Dockerfile

FROM python:3.10-slim

# 1) Install Kineto generator dependencies
WORKDIR /kineto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Install bash for entrypoint, plus cleanup
RUN apt-get update \
 && apt-get install -y bash \
 && rm -rf /var/lib/apt/lists/*

# 3) Copy the generator source
COPY . .

# 4) Install runtime + test dependencies
RUN pip install --no-cache-dir uvicorn pytest requests

# 5) Entrypoint setup
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["bash", "/entrypoint.sh"]
CMD ["--help"]
