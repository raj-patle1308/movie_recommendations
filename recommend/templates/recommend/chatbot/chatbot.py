import sys
import threading
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser, QLineEdit, QPushButton, QVBoxLayout, QWidget, \
    QLabel
from PyQt5.QtGui import QIcon, QFont
import speech_recognition as sr
import pyttsx3
from nltk.chat.util import Chat, reflections
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load movie data
movie_data = pd.read_csv('recommend/templates/recommend/chatbot/movies.csv')

# Drop duplicate rows
movie_data = movie_data.drop_duplicates()

# Clean genre column
movie_data['Genre'] = movie_data['Genre'].str.strip()

# Initialize CountVectorizer
count_vectorizer = CountVectorizer()

# Fit and transform the data
count_matrix = count_vectorizer.fit_transform(movie_data['Genre'])

# Compute cosine similarity matrix
cosine_sim = cosine_similarity(count_matrix, count_matrix)


# Function to recommend movies based on genre
def recommend_movies_by_genre(genre, movie_data=movie_data, cosine_sim=cosine_sim, top_n=5):
    idx = movie_data[movie_data['Genre'].str.contains(genre, case=False)].index
    if len(idx) == 0:
        return []
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_indices = [i[0] for i in sim_scores[1:top_n + 1]]
    recommended_movies = movie_data.iloc[sim_indices]['Film'].tolist()
    return recommended_movies


# Create a dictionary to store movies by genre
movies_by_genre = {}
for genre in movie_data['Genre'].unique():
    movies_by_genre[genre.lower()] = movie_data[movie_data['Genre'].str.lower() == genre.lower()]['Film'].tolist()

# Print lists for each genre
for genre, movies in movies_by_genre.items():
    print(f"{genre.capitalize()} movies:")
    for movie in movies:
        print(f"- {movie}")
    print()

# Modified rules to include movie recommendation
rules = [
    (r'hi|hello|hey', ['Hello!', 'Hi there!']),
    (r'(.*) (movies like) (.*)',
     lambda x, y=recommend_movies_by_genre: f'Recommended movies for {x[2]}: {", ".join(y(x[2]))}'),
    (r'thank you|thanks',
     ['You\'re welcome!', 'No problem, happy to help!', 'Anytime! If you have more questions, feel free to ask.']),
]

chatbot = Chat(rules, reflections)


class ChatbotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.recognizer = sr.Recognizer()
        self.speech_engine = pyttsx3.init()
        self.listening = False
        self.conversation_state = 0

    def init_ui(self):
        # Assuming self is an instance of QMainWindow
        icon = QIcon("recommend/templates/recommend/chatbot/movies.png")  # Replace "movies.png" with the path to your icon file
        self.setWindowIcon(icon)
        self.setWindowTitle('Movies recommendations')
        self.setGeometry(387, 165, 1149, 748)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.chat_display = QTextBrowser()
        layout.addWidget(self.chat_display)

        self.user_input = QLineEdit()
        self.user_input.returnPressed.connect(self.get_response)
        layout.addWidget(self.user_input)

        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.get_response)
        layout.addWidget(self.send_button)

        self.voice_input_button = QPushButton('Voice Input')
        self.voice_input_button.clicked.connect(self.process_voice_input)
        layout.addWidget(self.voice_input_button)

        self.voice_input_label = QLabel()
        layout.addWidget(self.voice_input_label)

        self.stop_button = QPushButton('Stop Listening')
        self.stop_button.clicked.connect(self.stop_listening)
        layout.addWidget(self.stop_button)

        self.exit_button = QPushButton('Exit Conversation')
        self.exit_button.clicked.connect(self.Exit_conv)
        layout.addWidget(self.exit_button)

        central_widget.setLayout(layout)

        self.set_window_style()
        self.add_icons()

    def set_window_style(self):
        # Add custom styling here
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTextBrowser, QLineEdit {
                background-color: white;
                border: 2px solid #3498db; /* Change border thickness and color */
                border-radius: 10px; /* Increase border radius for smoother edges */
                padding: 10px;
                font-size: 16px; /* Increase font size for better readability */
                color: #2c3e50; /* Change text color */
            }
            QPushButton {
                background-color: #27ae60; /* Change button color */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219d53; /* Darken button color on hover */
            }
        """)

    def add_icons(self):
        # Add icons to buttons
        self.send_button.setIcon(QIcon('recommend/templates/recommend/chatbot/send_icon.png'))
        self.voice_input_button.setIcon(QIcon('recommend/templates/recommend/chatbot/mic_icon.png'))
        self.stop_button.setIcon(QIcon('recommend/templates/recommend/chatbot/stop_icon.png'))
        self.exit_button.setIcon(QIcon('recommend/templates/recommend/chatbot/exit_icon.png'))

        # Adjust icon size
        icon_size = QSize(24, 24)
        self.send_button.setIconSize(icon_size)
        self.voice_input_button.setIconSize(icon_size)
        self.stop_button.setIconSize(icon_size)
        self.exit_button.setIconSize(icon_size)

    def Exit_conv(self):
        self.close()

    def get_response(self):
        user_input = self.user_input.text()
        response = ""

        if self.conversation_state == 0:
            response = "Hello! May I know your name, please?"
            self.conversation_state = 1

        elif self.conversation_state == 1:
            user_name = user_input.strip()
            if user_name:
                self.user_name = user_name
                response = f"Nice to meet you, {user_name}! What is your age?"
                self.conversation_state = 2
            else:
                response = "I didn't catch your name. Please enter your name."

        elif self.conversation_state == 2:
            user_age = user_input.strip()
            if user_age.isdigit():
                self.user_age = user_age
                response = "What is your gender (e.g., Male, Female, Other)?"
                self.conversation_state = 3
            else:
                response = "Please provide a valid age."

        elif self.conversation_state == 3:
            user_gender = user_input.strip()
            if user_gender.lower() in ["male", "female", "other"]:
                self.user_gender = user_gender
                response = "You can simply say 'No' to end the conversation. If you'd like movie recommendations, just type 'Movie recommendations'."
                self.conversation_state = 4
            else:
                response = "Please provide a valid gender (e.g., Male, Female, Other)."

        elif self.conversation_state == 4:

            if user_input.strip().lower() in ["no", "nope"]:
                response = f"Alright, {self.user_name}! If you ever need assistance in the future, feel free to ask. Have a great day!"

            elif user_input.strip().lower() == "movie recommendations":
                response = "Sure! What genre are you interested in?"
                self.conversation_state = 6  # Update conversation state to 6 for genre input

            else:
                response = chatbot.respond(user_input)
                self.conversation_state = 5  # Update conversation state to 5 for general conversation

        elif self.conversation_state == 5:
            response = "Alright! Is there anything else I can assist you with today?"
            self.conversation_state = 4  # Transition back to state 4 after general conversation

        elif self.conversation_state == 6:
            genre = user_input.strip().lower()
            if genre in movies_by_genre:
                movies = movies_by_genre[genre]
                response = f"Movies in the {genre} genre: {', '.join(movies)}."
            else:
                response = f"No movies found for genre {genre}."
            # Append movies to chat display
            self.chat_display.append(f'You: {user_input}')
            self.chat_display.append(f'Chatbot: {response}')
            threading.Thread(target=self.speak, args=(response,)).start()
            self.conversation_state = 5  # Transition back to state 4 after displaying movies

        if not response.startswith('Movies in the') and self.conversation_state != 5:
            self.chat_display.append(f'You: {user_input}')
            self.chat_display.append(f'Chatbot: {response}')
            threading.Thread(target=self.speak, args=(response,)).start()

        self.user_input.clear()

    def start_listening(self):
        self.listening = True
        self.voice_input_label.setText("Listening for voice input...")

        def voice_input_thread():
            try:
                with sr.Microphone() as source:
                    audio = self.recognizer.listen(source)
                    if self.listening:
                        voice_input = self.recognizer.recognize_google(audio)
                        print("Voice Input:", voice_input)
                        self.voice_input_label.setText(f"Voice Input: {voice_input}")
                        self.user_input.setText(voice_input)
                        self.get_response()
                    else:
                        print("Listening stopped.")
            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

        threading.Thread(target=voice_input_thread).start()

    def process_voice_input(self):
        self.start_listening()

    def stop_listening(self):
        self.listening = False
        self.voice_input_label.setText("Voice input listening stopped.")

    def speak(self, text):
        self.speech_engine.say(text)
        self.speech_engine.runAndWait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatbotWindow()
    window.show()
    sys.exit(app.exec_())
