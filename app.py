from flask import Flask, request, render_template, jsonify
import os
from transformers import pipeline
from dotenv import load_dotenv
import importlib.metadata

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize sentiment analysis pipeline with the multilingual model
# Get Hugging Face API key from .env file
hf_api_key = os.getenv("HF_API_KEY")
sentiment_analyzer = pipeline("text-classification", 
                             model="tabularisai/multilingual-sentiment-analysis", 
                             token=hf_api_key)

# Initialize Groq client - with better error handling for different versions
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = None

# Get the installed version of groq
groq_version = importlib.metadata.version('groq')
print(f"Using groq version: {groq_version}")

try:
    # Try the standard import
    from groq import Groq
    groq_client = Groq(api_key=groq_api_key)
except TypeError as e:
    if 'proxies' in str(e):
        # The error is related to the 'proxies' keyword
        print("Detected proxies issue, using alternative initialization method")
        try:
            # Try to import with environment variable
            os.environ["GROQ_API_KEY"] = groq_api_key
            from groq import Groq
            groq_client = Groq()
        except Exception as alt_e:
            print(f"Alternative initialization failed: {alt_e}")
            # Final fallback - try to use the client directly
            from groq.client import Groq as OldGroq
            groq_client = OldGroq(api_key=groq_api_key)
except Exception as e:
    print(f"Unexpected error initializing Groq client: {e}")
    # If everything else fails, use an older import pattern
    try:
        from groq.client import Groq as OldGroq
        groq_client = OldGroq(api_key=groq_api_key)
    except Exception as final_e:
        print(f"FATAL: Could not initialize Groq client: {final_e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        journal_entry = data['entry']
        
        if not journal_entry.strip():
            return jsonify({'success': False, 'error': 'Journal entry cannot be empty'})
        
        # Sentiment analysis using the multilingual model
        sentiment_result = sentiment_analyzer(journal_entry)[0]
        sentiment = sentiment_result['label']
        score = sentiment_result['score']
        
        # Converting sentiment labels (may be different from previous model)
        # The multilingual model returns "positive", "neutral", or "negative" as labels
        mood_map = {
            "positive": "positive",
            "neutral": "neutral",
            "negative": "negative"
        }
        
        mood = mood_map.get(sentiment.lower(), sentiment.lower())
        score_rounded = round(score * 100)
        
        # Groq API prompt
        prompt = f"""
        You are Lotus, an empathetic AI journal companion. Generate a detailed, warm, and deeply personalized response (approximately 400-500 words) to the user's journal entry below.
        
        The user's sentiment analysis shows: {sentiment} with {score_rounded}% confidence, but go beyond this simple classification.
        
        Your response MUST include:
        
        1. A thoughtful, detailed analysis (2-3 paragraphs) of their specific emotions, capturing nuances beyond the general sentiment. Identify particular feelings they're experiencing based on their exact words, tone, and subtext. For example, are they feeling frustrated but hopeful? Anxious but determined? Identify the complex emotional layers.
        
        2. A genuine, empathetic acknowledgment (2 paragraphs) that references at least 3-4 specific details from their entry to show you truly understand their unique situation. Reflect their own language patterns and terminology back to them. Connect emotionally with their experience.
        
        3. 3-4 personalized activities specifically tailored to their situation. These MUST be detailed suggestions (not generic advice) that directly address their specific circumstances, using details from their entry. For example:
           - Don't just suggest "try meditation" - suggest a specific 5-minute meditation focusing on the particular work anxiety they mentioned
           - Don't just suggest "practice self-care" - recommend a specific self-care ritual based on interests or preferences they mentioned
           - Each suggestion should be 3-4 sentences with specific guidance
        
        4. End with a warm, encouraging conclusion that references something specific from their entry and offers genuine hope.
        
        Make your response feel like it comes from a supportive friend who really knows them. Use conversational, warm language that matches their style. Include meaningful follow-up questions that encourage reflection.
        
        Format your response in HTML paragraphs with <p> tags for each section. Use <strong> tags for emphasis where appropriate.
        
        Journal entry: "{journal_entry}"
        """
        
        try:
            # Call Groq API with fallback
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=1.0,
                max_tokens=2000
            ).choices[0].message.content
        except Exception as api_error:
            # Create a more detailed fallback response
            keywords = journal_entry.lower().split()
            
            # Set fallback_mood based on sentiment analysis result
            fallback_mood = mood  # Using the already defined 'mood' variable
            
            # Extract potential emotional themes and specific details from journal
            # More detailed keyword analysis
            stress_words = any(word in journal_entry.lower() for word in ["stress", "anxiety", "worried", "overwhelmed", "pressure", "tense", "nervous", "panic"])
            sadness_words = any(word in journal_entry.lower() for word in ["sad", "down", "depressed", "unhappy", "lonely", "miss", "grief", "loss", "hurt"])
            happiness_words = any(word in journal_entry.lower() for word in ["happy", "joy", "excited", "grateful", "wonderful", "pleased", "delighted", "content"])
            relationship_words = any(word in journal_entry.lower() for word in ["friend", "partner", "family", "relationship", "boyfriend", "girlfriend", "husband", "wife", "mom", "dad", "parent", "child"])
            work_words = any(word in journal_entry.lower() for word in ["work", "job", "career", "boss", "project", "deadline", "colleague", "office", "meeting"])
            sleep_words = any(word in journal_entry.lower() for word in ["sleep", "tired", "insomnia", "rest", "exhausted", "fatigue", "bed", "dream"])
            health_words = any(word in journal_entry.lower() for word in ["health", "sick", "pain", "doctor", "illness", "symptom", "body", "physical"])
            future_words = any(word in journal_entry.lower() for word in ["future", "plan", "goal", "dream", "aspiration", "hope", "worry about", "uncertain"])
            
            # Look for specific activities mentioned
            exercise_mention = any(word in journal_entry.lower() for word in ["exercise", "workout", "run", "gym", "walk", "yoga", "fitness"])
            meditation_mention = any(word in journal_entry.lower() for word in ["meditate", "meditation", "mindfulness", "breathe", "breathing", "calm"])
            creative_mention = any(word in journal_entry.lower() for word in ["art", "write", "create", "music", "play", "paint", "draw", "sing", "creative"])
            nature_mention = any(word in journal_entry.lower() for word in ["nature", "outside", "outdoors", "park", "garden", "hike", "trees", "plants"])
            
            # Detect specific emotions beyond positive/negative
            frustration = any(word in journal_entry.lower() for word in ["frustrat", "annoy", "irritate", "upset", "bothered"])
            hope = any(word in journal_entry.lower() for word in ["hope", "optimistic", "looking forward", "better", "improve"])
            confusion = any(word in journal_entry.lower() for word in ["confus", "uncertain", "not sure", "don't know", "unclear", "lost"])
            gratitude = any(word in journal_entry.lower() for word in ["grateful", "thankful", "appreciate", "blessed"])
            
            # Extract specific themes to personalize exercises
            themes = []
            if stress_words: themes.append("stress")
            if sadness_words: themes.append("sadness")
            if happiness_words: themes.append("happiness")
            if relationship_words: themes.append("relationships")
            if work_words: themes.append("work")
            if sleep_words: themes.append("sleep")
            if health_words: themes.append("health")
            if future_words: themes.append("future planning")
            
            # Detect preferences/interests for personalization
            interests = []
            if exercise_mention: interests.append("physical activity")
            if meditation_mention: interests.append("mindfulness")
            if creative_mention: interests.append("creative expression")
            if nature_mention: interests.append("nature")
            
            # Define personalized exercises based on combination of themes and interests
            personalized_exercises = []
            
            # Work-related exercises
            if "work" in themes:
                if frustration:
                    personalized_exercises.append("Try the 'Three Good Things at Work' exercise: At the end of each workday this week, write down three things that went well at work, no matter how small. For each positive event, note your role in it. This practice can help rebalance your perspective when work frustrations feel overwhelming.")
                
                if "stress" in themes:
                    personalized_exercises.append("Practice the '90-second pause' technique when work stress arises: Set a timer for 90 seconds and focus only on your breathing while acknowledging the stress sensation in your body. Research shows most emotional reactions biochemically last about 90 seconds if we don't continue to feed them with thoughts. This gives you a reset button during challenging workdays.")
                
                personalized_exercises.append("Create a 'work containment ritual' to separate your professional and personal life. At the end of your workday, write down your top three priorities for tomorrow, then physically close your laptop or put away work materials while saying 'Work is complete for today.' This creates a psychological boundary that can prevent work stress from spilling into your personal time.")
            
            # Relationship-focused exercises
            if "relationships" in themes:
                if "sadness" in themes:
                    personalized_exercises.append("Write a 'connection letter' (unsent) to the person you're missing or having challenges with. Express your feelings honestly without judgment, then ask yourself what core need is being revealed through these emotions. Often, relationship difficulties point to important values like security, recognition, or understanding.")
                
                personalized_exercises.append("Practice 'active listening plus' in your next important conversation: Give your full attention, avoid interrupting, and summarize what you've heard. Then add the 'plus' - ask one curious question that invites deeper sharing. This demonstrates genuine interest beyond just hearing words.")
            
            # Sleep and rest exercises
            if "sleep" in themes:
                personalized_exercises.append("Try the '4-7-8 breathing technique' before bed: Inhale quietly through your nose for 4 seconds, hold your breath for 7 seconds, then exhale completely through your mouth for 8 seconds. Repeat 4 times. This pattern helps activate your parasympathetic nervous system, countering the sleep-disrupting effects of stress.")
                
                personalized_exercises.append("Create a 'worry drop' ritual before sleep: Keep a dedicated notepad by your bed. When racing thoughts arise, write them down completely, then visualize physically placing them in a container until morning. Tell yourself, 'I've saved these thoughts and can address them tomorrow with a fresher mind.'")
            
            # Health-focused exercises
            if "health" in themes:
                personalized_exercises.append("Practice a 3-minute body appreciation scan: Starting at your feet and moving upward, acknowledge something each part of your body allows you to do, regardless of pain or limitation. This shifts focus from what's wrong to what's still working, which research shows can actually reduce perceived pain intensity.")
                
                if "stress" in themes:
                    personalized_exercises.append("Try 'symptom scheduling' for health anxiety: Set aside 5-10 minutes twice daily to focus completely on physical sensations and health concerns. Outside these times, when health worries arise, gently remind yourself they'll be addressed during the next scheduled session. This prevents health concerns from constantly interrupting your day.")
            
            # Future planning exercises
            if "future planning" in themes:
                if confusion:
                    personalized_exercises.append("Use the 'Values Compass' exercise: List 5-7 core values (like connection, growth, security, etc.) Then rate how satisfied you feel with each one currently (1-10) and identify one small action for your highest priority value. When feeling uncertain about the future, this reconnects you with what matters most.")
                
                if hope:
                    personalized_exercises.append("Create a 'possibility portfolio' where you write down different versions of your future without judging them. Include scenarios you're excited about alongside ones you're afraid of. For each, note one small step you could take to explore it. This transforms vague future anxiety into concrete options.")
            
            # Exercises based on detected interests
            if "creative expression" in interests:
                personalized_exercises.append("Try 'emotional color mapping': Choose colors that represent different feelings you're experiencing. Without planning, create an abstract image using these colors. Once complete, notice which colors dominate, which are in conflict, and where they harmonize. This provides visual insight into your emotional landscape.")
            
            if "nature" in interests:
                personalized_exercises.append("Practice 'sensory nature immersion': Find a natural space (even a small park or garden) and spend 10 minutes systematically noticing something new through each sense. What subtle sounds, textures, or scents have you overlooked before? Research shows this practice reduces stress hormones more effectively than the same time spent in urban settings.")
            
            if "physical activity" in interests and "stress" in themes:
                personalized_exercises.append("Incorporate 'micro-movements' throughout your day: Set a timer for once each hour and do 60 seconds of gentle movement (stretching, marching in place, or dancing to one song). These brief physical interludes interrupt stress cycles and release tension that accumulates when we're stationary.")
            
            if "mindfulness" in interests:
                if confusion:
                    personalized_exercises.append("Practice the 'RAIN' technique when feeling overwhelmed: Recognize the emotion, Allow it to be there without judgment, Investigate where you feel it in your body, and Nurture yourself with self-compassion. This approach helps you relate differently to difficult emotions without being controlled by them.")
            
            # General emotional wellbeing exercises if no specific themes detected
            if not themes:
                if frustration:
                    personalized_exercises.append("Try the 'alternative perspectives' exercise: Write down a situation that's frustrating you. Then write three completely different interpretations of the same event. This cognitive flexibility practice helps reduce the feeling that your initial negative interpretation is the only possible truth.")
                
                if gratitude:
                    personalized_exercises.append("Practice 'specific gratitude': Instead of just listing what you're grateful for, describe exactly how it affects you. For example, rather than 'I'm grateful for my friend,' try 'I'm grateful for how my friend remembered that small detail about my preference, which made me feel truly seen.' This depth amplifies the positive emotional impact.")
                
                personalized_exercises.append("Experiment with a 'values-based decision filter': Identify your top three personal values (such as connection, growth, authenticity, etc.) When facing choices, ask yourself which option best honors these values. This creates clarity when you feel conflicted about what to do next.")
            
            # If we somehow don't have enough exercises, add some general ones
            while len(personalized_exercises) < 3:
                general_exercises = [
                    "Try a brief self-compassion practice: Place your hand on your heart, take three deep breaths, and tell yourself, 'This is a moment of difficulty. Difficulty is part of living. May I be kind to myself in this moment.' Research shows this simple practice can reduce stress hormones and increase feelings of connection.",
                    "Experiment with 'mental subtraction': Identify something positive in your life, then imagine it never happened. Consider how different your life would be without this person, experience, or opportunity. This practice counteracts hedonic adaptation—our tendency to take positive aspects of life for granted.",
                    "Practice the '3-3-3 grounding technique' when feeling overwhelmed: Name 3 things you can see, 3 things you can hear, and move 3 parts of your body. This simple exercise activates different parts of your brain and nervous system, creating an immediate shift in your emotional state."
                ]
                for exercise in general_exercises:
                    if exercise not in personalized_exercises:
                        personalized_exercises.append(exercise)
                        if len(personalized_exercises) >= 3:
                            break
            
            # Limit to 3 exercises
            personalized_exercises = personalized_exercises[:3]
            
            # Create fallback response with personalized exercises
            fallback_response = f"""
            <p>Thank you for sharing your thoughts with me today. I notice from your journal entry that you're experiencing some {fallback_mood} emotions.</p>
            
            <p>Your words reveal layers of what you're going through right now. I sense this is an important moment for reflection on the feelings you've expressed.</p>
            
            <p>I appreciate the vulnerability and thoughtfulness in your writing. The way you've articulated your experience shows a level of self-awareness that's really valuable.</p>
            
            <p><strong>Based on what you've shared, here are some personalized practices that might support you:</strong></p>
            """
            
            # Add personalized exercises
            for i, exercise in enumerate(personalized_exercises, 1):
                fallback_response += f"<p>{i}. {exercise}</p>"
            
            fallback_response += """
            <p>Remember that your feelings are valid, and it's okay to experience the full range of emotions. I'm here whenever you need to reflect or process what's happening in your life.</p>
            """
            
            response = fallback_response
            print(f"API Error: {str(api_error)}")
        
        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'score': score_rounded,
            'response': response
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)