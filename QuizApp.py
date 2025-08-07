import tkinter as tk
from tkinter import messagebox
import requests
import re

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Quiz Game (OpenRouter Edition)")
        self.root.geometry("900x600")  # Bigger window

        self.api_key = "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"  # 🔐 Replace with your real key
        self.model = "mistralai/mistral-7b-instruct"   # ✅ You can change to gpt-4, llama3, claude, etc.

        self.participants = []
        self.scores = {}
        self.questions = []
        self.current_question_index = 0
        self.current_team_index = 0
        self.num_questions = 5

        self.build_ui()

    def build_ui(self):
        # Top Section
        tk.Label(self.root, text="Enter Quiz Topic:").pack()
        self.topic_entry = tk.Entry(self.root, width=50)
        self.topic_entry.pack(pady=5)

        self.num_q_label = tk.Label(self.root, text="Number of Questions:")
        self.num_q_label.pack()

        self.num_q_entry = tk.Entry(self.root)
        self.num_q_entry.insert(0, "5")  # Default value
        self.num_q_entry.pack()

        tk.Label(self.root, text="Add Participant/Team:").pack()
        self.participant_entry = tk.Entry(self.root, width=30)
        self.participant_entry.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add Team", command=self.add_participant)
        self.add_button.pack()

        self.start_button = tk.Button(self.root, text="Start Quiz", command=self.start_quiz)
        self.start_button.pack(pady=10)

        # Quiz display
        self.quiz_frame = tk.Frame(self.root)
        self.quiz_frame.pack(pady=10, fill="both", expand=True)

        self.question_text = tk.Label(self.quiz_frame, text="", font=("Arial", 16), wraplength=700, justify="left")
        self.question_text.pack(pady=10)

        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(self.quiz_frame, text="", font=("Arial", 14), width=60, command=lambda i=i: self.check_answer(i))
            btn.pack(pady=5)
            self.answer_buttons.append(btn)

        # Scoreboard
        self.scoreboard_frame = tk.LabelFrame(self.root, text="Scoreboard", font=("Arial", 14))
        self.scoreboard_frame.pack(pady=10, fill="x")
        self.score_labels = {}  # Store label references per team

    def add_participant(self):
        name = self.participant_entry.get().strip()
        if name:
            self.participants.append(name)
            self.scores[name] = 0
            score_label = tk.Label(self.scoreboard_frame, text=f"{name}: 0", font=("Arial", 12), anchor="w")
            score_label.pack(fill="x", padx=10)
            self.score_labels[name] = score_label
            self.participant_entry.delete(0, tk.END)
            self.update_scoreboard()
        else:
            messagebox.showwarning("Input Error", "Team name cannot be empty.")

    def start_quiz(self):
        topic = self.topic_entry.get().strip()
        if not topic or not self.participants:
            messagebox.showerror("Error", "Please enter a topic and at least one participant.")
            return
        try:
            self.num_questions = int(self.num_q_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Number of questions must be an integer.")
            return

        self.questions = self.generate_questions(topic, self.num_questions)
        self.current_question_index = 0
        self.current_team_index = 0
        self.show_question()

    def generate_questions(self, topic, num_q):
        prompt = f"""
        Generate {num_q} multiple choice quiz questions on the topic '{topic}'.
        Each question should have:
        - 1 correct answer
        - 3 incorrect answers
        Format:
        Q: Question?
        A. Option A
        B. Option B
        C. Option C
        D. Option D
        Answer: A
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://yourdomain.com",
            "X-Title": "AI Quiz Game"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            return self.parse_questions(content)
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to get questions: {e}")
            return []

    def parse_questions(self, text):
        questions = []
        blocks = re.split(r"Q\d*[:.]", text)
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 6:
                continue
            q = lines[0]
            options = lines[1:5]
            answer_line = [line for line in lines if "Answer" in line]
            if not answer_line:
                continue
            match = re.search(r"Answer\s*[:\-]?\s*([A-D])", answer_line[0], re.IGNORECASE)
            if not match:
                continue

            answer_letter = match.group(1).upper()
            correct_index = ord(answer_letter) - ord("A")
            questions.append({
                "question": q,
                "options": [opt[2:].strip() for opt in options],
                "correct_index": correct_index
            })
        return questions

    def show_question(self):
        if self.current_question_index >= len(self.questions):
            self.question_text.config(text="Quiz complete!")
            for btn in self.answer_buttons:
                btn.pack_forget()
            self.update_scoreboard()
            return

        team = self.participants[self.current_team_index]
        q_data = self.questions[self.current_question_index]
        self.question_text.config(text=f"[{team}'s Turn]\n\nQ{self.current_question_index + 1}: {q_data['question']}")

        for i, opt in enumerate(q_data["options"]):
            self.answer_buttons[i].config(text=opt, state="normal")

    def check_answer(self, selected_index):
        q = self.questions[self.current_question_index]
        team = self.participants[self.current_team_index]

        if selected_index == q["correct_index"]:
            self.scores[team] += 1
            messagebox.showinfo("Correct!", f"Correct answer, {team}! +1 point.")
        else:
            messagebox.showinfo("Wrong!", f"Incorrect. The correct answer was: {chr(q['correct_index'] + 65)}")

        self.current_question_index += 1
        self.current_team_index = (self.current_team_index + 1) % len(self.participants)
        self.update_scoreboard()
        self.show_question()

    def update_scoreboard(self):
        max_score = max(self.scores.values(), default=0)
        for name in self.participants:
            score = self.scores[name]
            if score == max_score and max_score > 0:
                self.score_labels[name].config(text=f"{name}: {score}", fg="green", font=("Arial", 12, "bold"))
            else:
                self.score_labels[name].config(text=f"{name}: {score}", fg="black", font=("Arial", 12))


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()