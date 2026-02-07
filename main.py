import sqlite3
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import google.generativeai as genai

# ────────────────────────────────────────────────
#  === REPLACE WITH YOUR GEMINI API KEY ===
GEMINI_API_KEY = "AIzaSyAC2RX0QsQOm4BRbcq-OvJ7nGlqBELAo4g"
# ────────────────────────────────────────────────

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')  # Use the working model you chose

# -------------------------------
# Database Setup
# -------------------------------
def init_database():
    conn = sqlite3.connect('learning_platform.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic TEXT NOT NULL,
            concept TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database ready")

init_database()

# -------------------------------
# Database helpers
# -------------------------------
def register_user(username, password):
    conn = sqlite3.connect('learning_platform.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('learning_platform.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_progress(user_id, topic, concept, completed=False):
    conn = sqlite3.connect('learning_platform.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO progress (user_id, topic, concept, completed) VALUES (?, ?, ?, ?)",
                   (user_id, topic, concept, completed))
    conn.commit()
    conn.close()

# -------------------------------
# Gemini Functions
# -------------------------------
def get_ai_feedback(problem, approach):
    prompt = f"""
You are a patient programming tutor. Help the student understand deeply.

Problem: {problem}
Student's approach: {approach}

Evaluate:
- ✅ Fully correct
- ⚠️ Partially correct
- ❌ Incorrect

Explain gently: Praise good parts, point out deviations, guide without full code.
End with a hint or question.
Friendly tone, short.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def generate_mcqs(problem, num_questions=4):
    prompt = f"""
Based on this programming problem: {problem}

Generate {num_questions} MCQs to test concept understanding, edge cases, output prediction.
Each MCQ format:
Question: [question text]
Options:
A) [option]
B) [option]
C) [option]
D) [option]
Correct: [letter]
Explanation: [short why]

Make them educational, varied difficulty.
Output as plain text, one MCQ per block.
"""
    try:
        response = model.generate_content(prompt)
        # Parse the response into a list of dicts
        mcqs = []
        blocks = response.text.strip().split('\n\n')
        for block in blocks:
            lines = block.split('\n')
            if len(lines) < 7: continue
            q = lines[0].replace('Question: ', '').strip()
            opts = {lines[i][0]: lines[i][3:].strip() for i in range(1,5)}
            correct = lines[5].replace('Correct: ', '').strip()
            expl = lines[6].replace('Explanation: ', '').strip()
            mcqs.append({'question': q, 'options': opts, 'correct': correct, 'explanation': expl})
        return mcqs
    except Exception as e:
        return None

# -------------------------------
# Login Window
# -------------------------------
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Learning Platform - Login")
        self.root.geometry("450x400")
        self.root.resizable(False, False)

        tk.Label(root, text="Welcome!", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(root, text="Username:").pack()
        self.username_entry = tk.Entry(root, width=25)
        self.username_entry.pack(pady=5)
        tk.Label(root, text="Password:").pack()
        self.password_entry = tk.Entry(root, show="*", width=25)
        self.password_entry.pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=30)
        tk.Button(btn_frame, text="Login", command=self.login, width=12, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Register", command=self.register, width=12, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input required", "Enter both fields")
            return
        if register_user(username, password):
            messagebox.showinfo("Success", "Account created! Log in.")
        else:
            messagebox.showerror("Error", "Username exists")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input required", "Enter both fields")
            return
        user_id = login_user(username, password)
        if user_id:
            self.root.destroy()
            open_main_app(user_id, username)
        else:
            messagebox.showerror("Failed", "Wrong credentials")

# -------------------------------
# Main App Window
# -------------------------------
def open_main_app(user_id, username):
    root = tk.Tk()
    root.title(f"AI Learning - {username}")
    root.geometry("1100x900")
    root.minsize(1000, 800)

    tk.Label(root, text=f"Welcome back, {username}", font=("Arial", 18, "bold")).pack(pady=15)

    # Problem input
    tk.Label(root, text="Problem:", font=("Arial", 12, "bold")).pack(anchor="w", padx=30)
    problem_text = scrolledtext.ScrolledText(root, height=6, width=90, font=("Consolas", 11))
    problem_text.pack(pady=8, padx=30, fill="x")

    # Approach input
    tk.Label(root, text="Your understanding & approach:", font=("Arial", 12, "bold")).pack(anchor="w", padx=30, pady=(15,0))
    approach_text = scrolledtext.ScrolledText(root, height=9, width=90, font=("Consolas", 11))
    approach_text.pack(pady=8, padx=30, fill="x")

    # Feedback area
    tk.Label(root, text="AI Feedback:", font=("Arial", 12, "bold")).pack(anchor="w", padx=30, pady=(20,0))
    feedback_text = scrolledtext.ScrolledText(root, height=12, width=90, font=("Consolas", 11), state='disabled', bg="#f9f9f9")
    feedback_text.pack(pady=8, padx=30, fill="both", expand=False)

    # ────────────────────────────────────────────────
    # MCQ SECTION
    # ────────────────────────────────────────────────
    mcq_container = tk.Frame(root, padx=20, pady=10)
    mcq_container.pack(fill="both", expand=True, pady=20)
    mcq_container.pack_forget()  # hidden initially

    tk.Label(mcq_container, text="Practice Questions", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0,10))

    # Frame where questions will be added
    questions_frame = tk.Frame(mcq_container)
    questions_frame.pack(fill="both", expand=True)

    # Will store radio button variables
    answer_vars = []

    def show_mcqs(mcqs):
        # Clear previous content
        for widget in questions_frame.winfo_children():
            widget.destroy()
        answer_vars.clear()

        if not mcqs or not isinstance(mcqs, list) or len(mcqs) == 0:
            tk.Label(questions_frame, text="Could not generate questions.\nPlease try again or use a different problem.", fg="red", wraplength=800).pack(pady=20)
            return

        for i, mcq in enumerate(mcqs, 1):
            q_frame = tk.LabelFrame(questions_frame, text=f"Question {i}", padx=10, pady=10)
            q_frame.pack(fill="x", pady=12)

            tk.Label(q_frame, text=mcq["question"], wraplength=950, justify="left", font=("Arial", 11)).pack(anchor="w", pady=(0,5))

            var = tk.StringVar(value="")
            answer_vars.append(var)

            for letter in ['A', 'B', 'C', 'D']:
                if letter in mcq["options"]:
                    tk.Radiobutton(q_frame, text=f"{letter}) {mcq['options'][letter]}",
                                   variable=var, value=letter, font=("Arial", 10)).pack(anchor="w")

        # Submit button
        tk.Button(mcq_container, text="Check My Answers", command=lambda: check_answers(mcqs),
                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=20).pack(pady=20)

    def check_answers(mcqs):
        score = 0
        result_lines = []
        for i, (mcq, var) in enumerate(zip(mcqs, answer_vars), 1):
            selected = var.get()
            correct = mcq["correct"]
            expl = mcq["explanation"]

            if selected == correct:
                score += 1
                result_lines.append(f"Q{i}: ✅ Correct\n   {expl}\n")
            else:
                result_lines.append(f"Q{i}: ❌ Wrong (correct is {correct})\n   {expl}\n")

        result = f"Score: {score} / {len(mcqs)}\n\n" + "\n".join(result_lines)
        messagebox.showinfo("Results", result)

    # ────────────────────────────────────────────────
    # Buttons area
    # ────────────────────────────────────────────────
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)

    def get_feedback():
        problem = problem_text.get("1.0", tk.END).strip()
        approach = approach_text.get("1.0", tk.END).strip()

        if not problem or not approach:
            messagebox.showwarning("Missing input", "Please fill both the problem and your approach")
            return

        feedback_text.config(state="normal")
        feedback_text.delete("1.0", tk.END)
        feedback_text.insert(tk.END, "Thinking...\n\n")
        root.update_idletasks()

        feedback = get_ai_feedback(problem, approach)

        feedback_text.delete("1.0", tk.END)
        feedback_text.insert(tk.END, feedback)
        feedback_text.config(state="disabled")

        # Show the MCQ button only after feedback
        generate_mcqs_btn.pack(side=tk.LEFT, padx=20)

    tk.Button(btn_frame, text="Get Feedback", command=get_feedback,
              font=("Arial", 13, "bold"), bg="#FF5722", fg="white", width=20).pack(side=tk.LEFT, padx=10)

    def start_mcqs():
        problem = problem_text.get("1.0", tk.END).strip()
        if not problem:
            messagebox.showwarning("No problem", "Please enter a problem first")
            return

        mcqs = generate_mcqs(problem)
        print(f"Generated MCQs count: {len(mcqs) if mcqs else 0}")  # debug in terminal
        mcq_container.pack()  # make sure container is visible
        show_mcqs(mcqs)

    generate_mcqs_btn = tk.Button(btn_frame, text="Generate Practice MCQs", command=start_mcqs,
                                  font=("Arial", 13, "bold"), bg="#2196F3", fg="white", width=25)
    # Do NOT pack here — pack only after feedback

    root.mainloop()

# Start app
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()