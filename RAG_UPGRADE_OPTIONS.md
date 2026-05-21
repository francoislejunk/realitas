# RAG System Upgrade Options

The current RAG system uses a simple character n-gram based embedder with cosine similarity. This works well for Realitas Neo's current needs, but here are upgrade paths for production or larger-scale deployments:

---

## **Current System**

**SimpleEmbedder:**
- Character n-grams (3-letter chunks)
- TF-IDF weighting
- 1000-dimensional vectors
- Pure Python + NumPy (no external dependencies)

**Pros:**
- ✅ Fast and lightweight
- ✅ No external API calls
- ✅ Works offline
- ✅ Good enough for 100+ documents
- ✅ Zero cost

**Cons:**
- ❌ Less semantic understanding than neural models
- ❌ Doesn't understand synonyms or context well
- ❌ Limited to character-level patterns

---

## **Upgrade Option 1: Sentence Transformers**

**Library:** `sentence-transformers`

**Installation:**
```bash
pip install sentence-transformers
```

**Implementation:**
```python
from sentence_transformers import SentenceTransformer

class SentenceTransformerEmbedder:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def embed(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
    
    def fit(self, documents: List[str]):
        pass  # No fitting needed for pre-trained models
```

**Recommended Models:**
- `all-MiniLM-L6-v2` - Fast, 384 dimensions, good quality
- `all-mpnet-base-v2` - Best quality, 768 dimensions, slower
- `paraphrase-MiniLM-L6-v2` - Optimized for paraphrase detection

**Pros:**
- ✅ Much better semantic understanding
- ✅ Understands synonyms and context
- ✅ Pre-trained on massive datasets
- ✅ Still runs locally (no API calls)
- ✅ Free and open source

**Cons:**
- ❌ Requires ~100MB model download
- ❌ Slower than character n-grams
- ❌ Needs GPU for best performance (but works on CPU)

**When to use:**
- You have 500+ lore documents
- You need better semantic matching
- You want "bartender" to match "person serving drinks"

---

## **Upgrade Option 2: OpenAI Embeddings**

**API:** OpenAI Embeddings API

**Installation:**
```bash
pip install openai
```

**Implementation:**
```python
import openai

class OpenAIEmbedder:
    def __init__(self, api_key: str, model='text-embedding-3-small'):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def embed(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return np.array(response.data[0].embedding)
    
    def fit(self, documents: List[str]):
        pass  # No fitting needed
```

**Available Models:**
- `text-embedding-3-small` - 1536 dimensions, $0.02/1M tokens
- `text-embedding-3-large` - 3072 dimensions, $0.13/1M tokens
- `text-embedding-ada-002` - Legacy, 1536 dimensions, $0.10/1M tokens

**Pros:**
- ✅ Best quality embeddings available
- ✅ Excellent semantic understanding
- ✅ Multilingual support
- ✅ No local compute needed
- ✅ Always up-to-date

**Cons:**
- ❌ Costs money (though cheap)
- ❌ Requires internet connection
- ❌ API calls add latency
- ❌ Data sent to OpenAI servers

**When to use:**
- You need the absolute best quality
- You're already using OpenAI for LLM calls
- Cost isn't a concern ($0.02 per 1M tokens is very cheap)

---

## **Upgrade Option 3: Vector Databases**

For massive scale (10,000+ documents), use a dedicated vector database.

### **Pinecone**

**Cloud-hosted vector database**

```bash
pip install pinecone-client
```

```python
import pinecone

# Initialize
pinecone.init(api_key="your-key", environment="us-west1-gcp")
index = pinecone.Index("realitas-lore")

# Add documents
index.upsert(vectors=[
    ("doc1", embedding1, {"title": "...", "content": "..."}),
    ("doc2", embedding2, {"title": "...", "content": "..."})
])

# Search
results = index.query(query_embedding, top_k=5)
```

**Pros:**
- ✅ Handles millions of vectors
- ✅ Sub-millisecond search
- ✅ Managed service (no ops)
- ✅ Built-in filtering and metadata

**Cons:**
- ❌ Costs money (~$70/month for starter)
- ❌ Requires internet
- ❌ Overkill for small projects

### **Weaviate**

**Open-source vector database (can self-host)**

```bash
pip install weaviate-client
```

```python
import weaviate

client = weaviate.Client("http://localhost:8080")

# Create schema
client.schema.create_class({
    "class": "LoreDocument",
    "vectorizer": "text2vec-transformers"
})

# Add documents
client.data_object.create({
    "title": "...",
    "content": "..."
}, "LoreDocument")

# Search
results = client.query.get("LoreDocument", ["title", "content"]) \
    .with_near_text({"concepts": ["bartender jobs"]}) \
    .with_limit(5) \
    .do()
```

**Pros:**
- ✅ Open source, can self-host
- ✅ Built-in vectorization
- ✅ GraphQL API
- ✅ Scales to millions of documents

**Cons:**
- ❌ Requires Docker/infrastructure
- ❌ More complex setup
- ❌ Overkill for small projects

### **ChromaDB**

**Lightweight, embeddable vector database**

```bash
pip install chromadb
```

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("lore")

# Add documents
collection.add(
    documents=["content1", "content2"],
    metadatas=[{"title": "..."}, {"title": "..."}],
    ids=["doc1", "doc2"]
)

# Search
results = collection.query(
    query_texts=["bartender jobs"],
    n_results=5
)
```

**Pros:**
- ✅ Lightweight and easy to use
- ✅ Works locally (no server needed)
- ✅ Free and open source
- ✅ Good for 10K-100K documents

**Cons:**
- ❌ Not as fast as Pinecone/Weaviate at massive scale
- ❌ Limited filtering capabilities

---

## **Recommendation by Scale**

| Documents | Recommendation | Why |
|-----------|---------------|-----|
| < 100 | **Current system** | Fast, simple, good enough |
| 100-1,000 | **Sentence Transformers** | Better quality, still local |
| 1,000-10,000 | **OpenAI Embeddings + ChromaDB** | Best quality, manageable scale |
| 10,000+ | **OpenAI Embeddings + Pinecone** | Production-grade, scales infinitely |

---

## **Migration Path**

To upgrade the embedder, you only need to replace the `SimpleEmbedder` class:

```python
# In lore_rag_system.py, replace:
class LoreRAGSystem:
    def __init__(self, storage_directory: Path):
        # OLD:
        self.embedder = SimpleEmbedder()
        
        # NEW (Sentence Transformers):
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # NEW (OpenAI):
        from openai_embedder import OpenAIEmbedder
        self.embedder = OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY"))
```

The rest of the RAG system (search, storage, context generation) works identically!

---

## **Cost Comparison**

**Current System:**
- Cost: $0
- Speed: ~1ms per search
- Quality: Good

**Sentence Transformers:**
- Cost: $0 (one-time ~100MB download)
- Speed: ~10ms per search (CPU), ~2ms (GPU)
- Quality: Excellent

**OpenAI Embeddings:**
- Cost: ~$0.02 per 1M tokens (~$0.20 for 10K documents)
- Speed: ~50ms per search (API latency)
- Quality: Best

**Pinecone:**
- Cost: ~$70/month (starter tier)
- Speed: ~5ms per search
- Quality: Depends on embedder used

---

## **Bottom Line**

**For Realitas Neo right now:** The current system is perfect. It's fast, free, and works great for the scale you need.

**When to upgrade:** If you add 500+ lore documents or need better semantic matching (e.g., "person serving drinks" should match "bartender").

**Best upgrade path:** Sentence Transformers → keeps everything local, free, and significantly better quality.
