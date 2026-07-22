# IKIP Setup & User Guide

This guide explains how to spin up the Industrial Knowledge Intelligence Platform (IKIP) and test its core features.

## Prerequisites
- Docker & Docker Compose installed.
- An OpenAI API Key (`sk-...`).

## Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/1212ekta/ai-industrial.git
   cd ai-industrial
   ```
2. Copy `.env.example` to `.env` in the root folder and add your OpenAI Key:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   QDRANT_URL=http://qdrant:6333
   ```
3. Boot the environment:
   ```bash
   docker-compose up --build
   ```
4. Access the Platform:
   - **Frontend UI**: http://localhost:3000
   - **Backend API Docs**: http://localhost:8000/docs
   - **Neo4j Browser**: http://localhost:7474

## Using the Platform

### 1. Ingest Documents
Navigate to the **Upload Data** page. Upload a sample industrial document (e.g., a PDF manual for a Centrifugal Pump). The system will automatically chunk, embed (Qdrant), and map entities (Neo4j).

### 2. View the Knowledge Graph
Navigate to the **Knowledge Graph** page to see a visual map of the relationships (Equipment -> Failure -> Vendor) that the AI automatically extracted from your documents.

### 3. Ask the Copilot
Navigate to the **AI Copilot** page and ask a question (e.g., "What are the common failures for the Centrifugal Pump?"). The LangGraph AI will search both vector and graph databases to provide an accurate answer with citations.

### 4. Root Cause Analysis
Navigate to the **RCA** page. Input an equipment name and a reported problem. The AI will generate a structured analysis of likely causes and recommendations based on historical uploads.
