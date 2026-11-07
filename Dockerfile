FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HF_HOME=/opt/models \
    HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_XET=1 \
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./requirements.txt
# CPU wheels avoid installing GPU runtimes on a web server.
RUN python -m pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install --no-cache-dir -r requirements.txt
# Prepare and validate the default model during the build, not the professor's first query.
COPY src/embedding_onnx.py /tmp/embedding_onnx.py
RUN PYTHONPATH=/tmp python -c "from embedding_onnx import QuantizedMultilingualEmbeddings; model=QuantizedMultilingualEmbeddings(); assert len(model.embed_query('졸업인증'))==384"
ENV HF_HUB_OFFLINE=1
ENV EMBEDDING_BACKEND=onnx RAG_VECTOR_DEFAULT=1
COPY app.py deploy.py ./
COPY src ./src
COPY data ./data
COPY rules ./rules
COPY references ./references
COPY examples ./examples
COPY .streamlit ./.streamlit
RUN useradd --create-home appuser && chown -R appuser:appuser /app /opt/models
USER appuser
EXPOSE 8501
CMD ["python", "deploy.py"]
