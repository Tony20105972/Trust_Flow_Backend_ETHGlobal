# 🚀 Deployment Guide (Render/Fly.io)

This guide outlines the steps to deploy our backend application to cloud platforms like Render or Fly.io.

---

## **Prerequisites**

* A Render.com or Fly.io account.
* `git` installed on your local machine.
* Basic understanding of Python and Docker (though not strictly required for Render/Fly.io).
* Your project code pushed to a GitHub repository.

---

## **1. Environment Variables (.env)**

Crucially, **sensitive API keys and private keys must NOT be committed to your GitHub repository.** Instead, they should be configured as **environment variables** directly on your chosen deployment platform (Render/Fly.io).

Refer to your local `.env.example` file for a list of required environment variables:

* `PRIVATE_KEY`
* `GROQ_API_KEY`
* `OPENAI_API_KEY`
* `IPFS_API_KEY`
* *(Any other sensitive keys required by your application)*

**On Render:**
1.  Go to your service settings.
2.  Navigate to "Environment".
3.  Add each variable as a new key-value pair.

**On Fly.io:**
Use the `fly secrets set` command:
```bash
fly secrets set PRIVATE_KEY="your_private_key" GROQ_API_KEY="your_groq_key"
