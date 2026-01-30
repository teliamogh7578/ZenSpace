# 🧠 ZenSpace: The Algorithmic Wellness Guardian

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python) 
![Computer Vision](https://img.shields.io/badge/Computer_Vision-MediaPipe-orange?logo=google) 
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-green) 

> **"Code in Flow. Rest in Privacy."**

We've all been there: you sit down to code for "just an hour," and suddenly it's 3 AM, your back hurts, and you're mentally drained. 

**ZenSpace** is our answer to that. It’s not a chatbot or a cloud service. It’s a lightweight, **offline algorithmic system** that uses simple geometry to watch out for your well-being. It runs quietly in the background, analyzing video landmarks to help you maintain posture, reduce eye strain, and break bad habits—without ever sending a single pixel to the internet.

---

## 🌟 Why We Built This (And How It Helps)

### 🛡️ 1. Privacy by Design (No Cloud, Just Math)
Most "wellness apps" want your data. ZenSpace doesn't.
* **Algorithmic, Not Generative:** We don't use black-box LLMs. We use precise geometric algorithms (Euclidean distance between landmarks) to understand what's happening.
* **100% Local:** Your webcam feed is processed in your RAM and discarded instantly. Nothing leaves your laptop.

### 🔋 2. Algorithmic Fatigue Monitoring
Instead of annoying timers, we use computer vision to detect *actual* tiredness.
* **Yawn Counter:** Tracks the Mouth Aspect Ratio (MAR) to catch "micro-sleep" signals before you burn out.

### 🚫 3. Breaking Habits (The "Anti-Biting" Logic)
Do you bite your nails when debugging? (We do too).
* **Hand-to-Face Vectors:** The system tracks the coordinate distance between your fingertips and mouth.
* **Subtle Intervention:** If the distance drops below a threshold, it triggers a subtle screen tint or "brown noise" to gently nudge you to stop, without breaking your focus.

---

## 🏗️ Under the Hood: The Logic

ZenSpace follows a strict **Sensory-Compute-Actuate** algorithmic loop. It’s deterministic and lightweight.

graph TD
    A[Webcam Input] -->|Raw Frames| B(Main Loop)
    B -->|Grayscale Conv| C{MediaPipe Mesh}
    C -->|468 Face Points| D[Vector Math: Eyes/Mouth]
    C -->|21 Hand Points| E[Vector Math: Fingers]
    D & E -->|Threshold Logic| F[Decision Tree]
    F -->|Draw Overlay| G[Tkinter Canvas]
    F -->|Adjust Audio| H[System Volume API]
# 🛠️ Installation Guide for ZenSpace

This guide will help you set up **ZenSpace** on your local machine.

## ✅ Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.9 or higher**: [Download here](https://www.python.org/downloads/)
* **Git**: [Download here](https://git-scm.com/downloads)
* **A Webcam**: Built-in or USB.
* **OS**: Windows 10/11 (Required for *Gesture Volume Control* features).

---

## 🚀 Step-by-Step Setup

### 1. Clone the Repository
Open your terminal (Command Prompt, PowerShell, or VS Code Terminal) and run:

```bash
git clone [https://github.com/teliamogh7578/ZenSpace.git](https://github.com/teliamogh7578/ZenSpace.git)
cd ZenSpace
