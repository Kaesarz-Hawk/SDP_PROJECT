<div align="center">

# 🔥 Momentum

### **Personal Consistency & Productivity Operating System**

> **Turn goals into systems. Turn systems into habits. Build momentum.**

A polished, offline-first desktop productivity application built to help users **plan, track, visualize, and improve consistency** across different areas of life.

<br>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-7C5CFC?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Analytics-11557C?style=for-the-badge\&logo=python\&logoColor=white)
![PyInstaller](https://img.shields.io/badge/PyInstaller-Executable-FFD43B?style=for-the-badge\&logo=python\&logoColor=black)

<br>

**🌙 Dark UI • 📊 Analytics • 🔥 Streaks • 🗓️ Planning • 💾 Local Storage • ⚡ Windows EXE**

</div>

---

## ✦ What is Momentum?

**Momentum** is a desktop-based personal consistency and productivity system designed around one simple idea:

> **Progress becomes easier when it becomes measurable.**

Instead of treating productivity as a collection of disconnected to-do lists, Momentum connects:

**Tracks → Habits → Daily Logs → Tasks → Plans → Analytics → Streaks**

This creates a complete personal productivity loop where users can define larger goals, break them into trackable habits, manage daily tasks, monitor consistency, and understand their progress through visual analytics.

---

## 🚀 Core Features

### 🏠 Dashboard

A centralized overview of your current momentum.

* 📈 Overall completion progress
* 🔥 Active streak count
* ⭐ Best streak record
* 📊 Daily / Weekly / Monthly / Yearly views
* 🟪 30-day consistency heatmap
* 🎯 Individual habit cards
* ⚡ One-click habit completion
* 📉 Mini 7-day progress indicators

---

### 🔥 Habit Tracker

Track habits over time instead of relying on memory.

* Create and manage habits
* Assign habits to specific tracks
* Set target frequency
* Daily completion logging
* Current streak calculation
* All-time best streak calculation
* Historical consistency tracking
* Monthly habit matrix
* Habit-specific statistics

---

### 🗓️ Calendar

Understand **when** your consistency happens.

* Visual consistency calendar
* Daily habit inspection
* Historical completion data
* Day-by-day productivity overview
* Heatmap-based progress visualization

---

### ✅ Smart To-Do System

A task manager designed around actual daily execution.

* Create tasks
* Due dates
* Priority levels

  * 🟢 Low
  * 🟡 Medium
  * 🔴 High
* Task completion status
* Link tasks to productivity tracks
* Automatic incomplete-task rollover
* Carried-over task tracking

---

### 📊 Analytics

Turn your activity into useful information.

Momentum includes embedded **Matplotlib** analytics for:

* 📊 Weekly completion volume
* 📈 Monthly consistency trends
* 🍩 Category / track distribution
* 🏆 Top-performing habits
* ⚠️ Habits that need attention
* 📉 Consistency diagnostics

The goal isn't just to show numbers.

It's to answer:

> **"Where am I actually improving?"**

and

> **"What am I neglecting?"**

---

### 🧭 Goal Decomposition & Plan Builder

Large goals become easier when broken down.

The built-in plan builder allows users to:

1. Define a life / productivity track
2. Select a category
3. Customize its color and icon
4. Add individual habits or skills
5. Define target frequency
6. Set a long-term duration
7. Add notes and objectives
8. Create a structured plan

Example:

```text
Full-Stack Development
│
├── JavaScript
├── React
├── SQL
├── MongoDB
├── Backend
└── Competitive Programming
```

Instead of:

> "I want to become better at programming."

Momentum turns it into:

> **A measurable system with daily actions.**

---

### ⚙️ Settings & Data Management

* Application configuration
* Database management
* Data reset functionality
* Application information
* Persistent local storage
* Clean database shutdown

---

## 🧠 The Momentum System

The application is built around a layered productivity model:

```text
                 ┌─────────────────────┐
                 │      BIG GOALS      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       TRACKS        │
                 │  Life / Goal Areas  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       HABITS        │
                 │ Daily Behaviours    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    DAILY LOGS       │
                 │  Actual Execution   │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────────┐   ┌─────────────────┐
        │      TASKS      │   │   ANALYTICS     │
        │ Daily Execution │   │  Performance    │
        └─────────────────┘   └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │     STREAKS     │
                              │   CONSISTENCY   │
                              └─────────────────┘
```

---

## 🎨 Design Philosophy

Momentum uses a modern **dark productivity dashboard** aesthetic.

### Visual System

* Deep near-black background
* Elevated card surfaces
* Vibrant violet accent
* Emerald success states
* Amber warnings
* Red danger states
* Rounded cards
* Consistent spacing
* Segmented controls
* Progress rings
* Heatmaps
* Interactive charts

The UI is built around a centralized design system so that colors, typography, spacing, and component styling remain consistent throughout the application.

---

## 🏗️ Architecture

Momentum follows a modular structure rather than putting the entire application inside one Python file.

```text
SDP_PROJECT/
│
├── assets/
│   └── icon.ico
│
├── database/
│   └── db_manager.py
│
├── models/
│   ├── daily_log.py
│   ├── habit.py
│   ├── plan.py
│   ├── task.py
│   └── track.py
│
├── ui/
│   ├── app_controller.py
│   ├── dashboard_frame.py
│   ├── habit_tracker_frame.py
│   ├── calendar_frame.py
│   ├── todo_frame.py
│   ├── analytics_frame.py
│   ├── onboarding_frame.py
│   ├── settings_frame.py
│   ├── sidebar.py
│   │
│   └── components/
│       ├── habit_card.py
│       ├── heatmap_grid.py
│       ├── modal_dialog.py
│       └── progress_ring.py
│
├── utils/
│   ├── path_helper.py
│   ├── seed_data.py
│   ├── streak_calculator.py
│   └── theme.py
│
├── database/
│
├── main.py
├── verify_momentum.py
├── requirements.txt
├── BUILD.md
└── Momentum.spec
```

---

## 🗄️ Database Design

Momentum uses **SQLite** for local persistence.

The database contains interconnected entities for:

```text
Tracks
  │
  ├── Habits
  │     └── Daily Logs
  │
  ├── Tasks
  │
  └── Plans
```

### Main Tables

| Table        | Purpose                                       |
| ------------ | --------------------------------------------- |
| `tracks`     | Organize goals into life / productivity areas |
| `habits`     | Store recurring behaviours                    |
| `daily_logs` | Store daily completion history                |
| `tasks`      | Manage daily tasks and deadlines              |
| `plans`      | Store long-term plans and targets             |

Foreign keys and cascading relationships are used to maintain database consistency.

---

## 🔥 Streak Engine

Momentum includes a dedicated streak calculation module.

It calculates:

* **Current streak**
* **Best historical streak**
* Streak recovery from yesterday
* Consecutive completion sequences
* Visual streak intensity

Example:

```text
Mon  Tue  Wed  Thu  Fri
 ✅    ✅    ✅    ❌    ✅

Current Streak = 1
Best Streak    = 3
```

The streak logic is separated from the UI and database layer, making it easier to test and maintain.

---

## 🌱 First-Run Experience

Momentum automatically detects an empty database and generates realistic demonstration data.

The initial dataset includes:

* Multiple productivity tracks
* Multiple habits
* 30 days of historical completion data
* Sample tasks
* Different task priorities
* A long-term productivity plan

This means the application doesn't open as an empty dashboard.

Instead, users immediately get a populated environment that demonstrates how the system works.

---

## 🧪 Automated Verification

The project includes a dedicated verification suite:

```bash
python verify_momentum.py
```

The verification system checks:

* ✅ Streak calculations
* ✅ SQLite schema
* ✅ CRUD operations
* ✅ Foreign key behaviour
* ✅ Daily-log upserts
* ✅ Task rollover
* ✅ Seed data generation
* ✅ Asset paths
* ✅ Database paths
* ✅ UI screen instantiation
* ✅ Analytics rendering
* ✅ Zero-data states
* ✅ Database shutdown

The application is therefore tested beyond simply checking whether the main window opens.

---

## 🛠️ Tech Stack

### Core

* 🐍 **Python**
* 🎨 **CustomTkinter**
* 🗄️ **SQLite**

### Visualization

* 📊 **Matplotlib**

### Image / Asset Handling

* 🖼️ **Pillow**

### Packaging

* 📦 **PyInstaller**

### Architecture

* MVC-inspired separation
* Modular UI frames
* Dedicated database manager
* Dedicated data models
* Utility / business-logic modules
* Reusable UI components

---

## ⚡ Run Locally

### 1. Clone

```bash
git clone https://github.com/Kaesarz-Hawk/SDP_PROJECT.git
cd SDP_PROJECT
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

**Windows CMD:**

```cmd
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Launch Momentum

```bash
python main.py
```

---

## 📦 Build Standalone Windows `.exe`

Momentum can be packaged into a standalone executable using PyInstaller.

```bash
pyinstaller --noconfirm --onefile --windowed --name "Momentum" --icon=assets/icon.ico --add-data "assets;assets" main.py
```

The resulting executable will be available inside:

```text
dist/
└── Momentum.exe
```

The application is designed so that the packaged version stores mutable application data in:

```text
%LOCALAPPDATA%\Momentum\
```

This keeps the SQLite database separate from bundled application resources.

---

## 🖥️ Application Flow

```text
                    ┌──────────────┐
                    │    Splash    │
                    └──────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Dashboard    │
                  └───────┬─────────┘
                          │
       ┌──────────┬───────┼───────┬──────────┐
       ▼          ▼       ▼       ▼          ▼
    Habits     Calendar   To-Do  Analytics  Plans
       │          │       │       │          │
       └──────────┴───────┴───────┴──────────┘
                           │
                           ▼
                       Settings
```

---

## 🎯 Project Goals

Momentum was designed to explore how a relatively lightweight desktop application can combine:

* Software architecture
* GUI development
* Database management
* Data visualization
* Business logic
* Automated testing
* Application packaging
* User-centered design

The project focuses on creating something that is not simply a **CRUD application**, but a complete usable desktop product.

---

## 🔮 Future Possibilities

Potential future improvements include:

* ☁️ Optional cloud synchronization
* 📱 Mobile companion application
* 🤖 AI-powered productivity insights
* 📈 More advanced analytics
* 🔔 Desktop reminders
* 🎯 Goal recommendations
* 📤 Data export / import
* 🏆 Achievement system
* 🔐 Optional application-level authentication

---

## 👨‍💻 Development

Built as a **Software Development Project (SDP)** with a focus on practical software engineering, modular architecture, database-backed applications, and polished desktop UX.

---

<div align="center">

### 🔥 Don't chase motivation. Build Momentum.

**Plan → Execute → Track → Analyze → Improve**

<br>

Made with Python & ☕ by **Kaesarz-Hawk**

<br>

⭐ If you find the project interesting, consider giving it a star.

</div>
