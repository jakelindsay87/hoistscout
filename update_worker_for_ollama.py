#!/usr/bin/env python3
"""
Script to update worker environment variables for Ollama
Run this after deploying the Ollama proxy
"""
import os

print("=" * 60)
print("HoistScout Worker Configuration for Ollama")
print("=" * 60)
print()

print("After deploying the Ollama proxy service, update your worker")
print("environment variables in Render dashboard:")
print()

print("1. Go to your hoistscout-worker service in Render")
print("2. Click on 'Environment' tab")
print("3. Add/Update these variables:")
print()

print("OLLAMA_BASE_URL=https://hoistscout-ollama-proxy.onrender.com")
print("OLLAMA_MODEL=llama3.1")
print()

print("4. Click 'Save Changes'")
print("5. The worker will automatically restart and use Ollama")
print()

print("Alternative: For external Ollama server:")
print("OLLAMA_BASE_URL=http://your-ollama-server:11434")
print()

print("To verify it's working:")
print("1. Trigger a new scraping job")
print("2. Check worker logs for 'Extracting opportunities from ... using Ollama'")
print("3. Check extracted opportunities for detailed financial and eligibility data")
print()

print("The enhanced extraction will include:")
print("- Detailed financial information (min/max values, currencies)")
print("- Eligibility requirements and restrictions")
print("- Submission deadlines in proper ISO format")
print("- Contact information and submission methods")
print("- Assessment criteria and priority areas")
print("- Co-funding requirements")
print("- Geographic and sector restrictions")