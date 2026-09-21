# Skill Relationships & Transferability

## Container orchestration
Docker experience is a reasonable prerequisite for Kubernetes, but it is not
equivalent to it. Docker covers building and running individual containers;
Kubernetes covers scheduling, scaling, and networking many containers across
a cluster. A candidate with only Docker experience should be described as
having a transferable foundation, not as already possessing Kubernetes
experience.

## Cloud compute transitions
Experience with AWS EC2/S3 provides a transferable foundation for AWS ECS/EKS
or GCP/Azure equivalents, since the core cloud concepts (IAM, networking,
storage) carry over, but container-orchestration-specific services (ECS,
EKS, GKE) still require dedicated learning.

## Classical ML to deep learning to LLMs
scikit-learn / classical ML experience transfers conceptually to deep
learning (loss functions, train/val/test splits, evaluation metrics) but the
tooling (PyTorch/TensorFlow) and failure modes (overfitting at scale,
GPU memory) differ enough to warrant explicit deep learning experience for
DL-heavy roles.

## RAG and vector databases
Experience building a RAG pipeline (chunking, embedding, retrieval, LLM
grounding) is strong, directly relevant evidence for "vector database" and
"LLM orchestration" requirements, even if the specific vector DB technology
named in the JD (e.g. Pinecone) differs from the one used (e.g. Qdrant/FAISS)
— the underlying skill (approximate nearest neighbor search, embedding
similarity) transfers directly.

## Frontend to backend transitions
General API development, Git, and deployment experience gained in a
frontend-heavy role (e.g. calling REST APIs from React) is genuinely
relevant evidence for backend API development requirements, though it does
not substitute for server-side framework experience (FastAPI/Django/Spring).
