import streamlit as st
from openai import OpenAI
#from dotenv import dotenv_values
from supabase import create_client
import os
import json
import base64
import uuid
from datetime import datetime
#import shutil

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Generator Kolorowanek",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

#debug
st.write("APP STARTED")


#
#os.makedirs("history", exist_ok=True)





if not st.session_state.get("user"):
    st.stop()

# ---------------------------------------------------
# CSS
# ---------------------------------------------------

st.markdown("""
<style>

.stApp{
    background-color:#ffffff;
}

h1,h2,h3,h4,p,label{
    color:#111827;
}

.thumbnail {
    transition: transform 0.25s ease;
    border-radius: 12px;
}

.thumbnail:hover {
    transform: scale(1.12);
    z-index: 10;
    position: relative;
}

.cost-box{
    padding:10px;
    border-radius:10px;
    background:#1e293b;

}
.image-wrapper {
    position: relative;
}

.delete-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0,0,0,0.6);
    color: white;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    opacity: 0;
    transition: 0.2s;
    font-weight: bold;
}

.image-wrapper:hover .delete-btn {
    opacity: 1;
}

            

</style>
""", unsafe_allow_html=True)

# # Historia:
# HISTORY_FILE = "history.json"


# def load_history():
#     if os.path.exists(HISTORY_FILE):
#         with open(HISTORY_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return []


# def save_history(history):
#     with open(HISTORY_FILE, "w", encoding="utf-8") as f:
#         json.dump(history, f, ensure_ascii=False, indent=2)


# def zapisanie obrazka
# def save_image(base64_data, folder, filename):
#     import base64

#     os.makedirs(folder, exist_ok=True)

#     image_bytes = base64.b64decode(base64_data)

#     path = os.path.join(folder, filename)

#     with open(path, "wb") as f:
#         f.write(image_bytes)

#     return path
# ---------------------------------------------------
# OPENAI
# ---------------------------------------------------

# env = dotenv_values(".env")

# client = OpenAI(
#     api_key=env["OPENAI_API_KEY"]
# )

# API_KEY
if not st.session_state.get("openai_api_key"):
    # Najpierw szukamy klucza w bezpiecznych sekretach (lokalnie lub w Streamlit Cloud)
    if "OPENAI_API_KEY" in st.secrets:
        st.session_state["openai_api_key"] = st.secrets["OPENAI_API_KEY"]
    else:
        # Jeśli klucza nie ma w sekretach, prosimy użytkownika o wpisanie go ręcznie
        st.info("Dodaj swój klucz API OpenAI, aby móc korzystać z tej aplikacji")
        user_key = st.text_input("Klucz API", type="password")
        if user_key:
            st.session_state["openai_api_key"] = user_key
            st.rerun()

# Blokada aplikacji
if not st.session_state.get("openai_api_key"):
    st.stop()

# Inicjalizacja Klienta
openai_client = OpenAI(api_key=st.session_state["openai_api_key"])

# initializacja supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON_KEY"]
)


# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------

if "prompts" not in st.session_state:
    st.session_state.prompts = []

if "user" not in st.session_state:
    st.session_state.user = None

if "generated_images" not in st.session_state:
    st.session_state.generated_images = []

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

if "last_request_cost" not in st.session_state:
    st.session_state.last_request_cost = 0.0

if "selected_prompts" not in st.session_state:
    st.session_state.selected_prompts = []

if "last_selected" not in st.session_state:
    st.session_state.last_selected = []

if "generated_titles" not in st.session_state:
    st.session_state.generated_titles = set()

# if "history" not in st.session_state:
#     st.session_state.history = []

# if "history" not in st.session_state:

#     if os.path.exists("history.json"):

#         with open("history.json", "r", encoding="utf-8") as f:
#             st.session_state.history = json.load(f)

#     else:
#         st.session_state.history = []

if "confirm_delete_history" not in st.session_state:
    st.session_state.confirm_delete_history = False


user = st.session_state.get("user")

if "history" not in st.session_state:

    user = st.session_state.get("user")

    if user and getattr(user, "id", None):

        try:
            response = (
                supabase.table("history")
                .select("*")
                .eq("user_id", user.id)
                .order("id", desc=True)
                .limit(30)
                .execute()
            )

            st.session_state.history = response.data or []

        except Exception as e:
            st.session_state.history = []
            st.error(f"Błąd odczytu historii: {e}")

    else:
        st.session_state.history = []


# Log in
if not st.session_state.get("user"):

    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Hasło", type="password")

    if st.button("Zaloguj"):

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            st.session_state.user = response.user
            st.rerun()

        except Exception as e:
            st.error("Błąd logowania")

    st.stop()

# log Out
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# reset hasła
st.subheader("🔑 Reset hasła")

reset_email = st.text_input("Email do resetu", key="reset_email")

if st.button("Wyślij link resetujący"):

    try:
        supabase.auth.reset_password_email(reset_email)
        st.success("Link resetujący został wysłany na email.")

        

    except Exception as e:
        st.error(f"Błąd resetu hasła: {e}")



# rejestracja
st.subheader("🆕 Rejestracja")

new_email = st.text_input("Nowy email", key="reg_email")
new_password = st.text_input("Nowe hasło", type="password", key="reg_pass")

if st.button("Utwórz konto"):

    try:
        response = supabase.auth.sign_up({
            "email": new_email,
            "password": new_password
        })

        st.success("Konto utworzone! Sprawdź email i potwierdź rejestrację.")

    except Exception as e:
        st.error(f"Błąd rejestracji: {e}")
st.success("Konto utworzone! Sprawdź email i potwierdź rejestrację.")
st.info("Po potwierdzeniu możesz się zalogować.")


#wyszukiwarka pomyłów
st.title("🎨 Generator Kolorowanek")

col1, _ = st.columns([2, 1])

with col1:
    theme = st.text_input(
        "Motyw kolorowanek",
        placeholder="np. Dinozaury"
    )

    #wybór poziomu
    level = st.segmented_control(
        "Poziom",
        options=[
            "🧒 Dzieci",
            "🧑 Starsze",
            "🧘 Dorośli"
        ],
        default="🧒 Dzieci"
    )

    # styl
    style = st.segmented_control(
        "Styl",
        options=[
            "🎭 Cartoon",
            "🌸 Kawaii",
            "🐉 Fantasy",
            "🦖 Realistic",
            "🧘 Mandala"
        ],
        default="🎭 Cartoon"
    )

    generate_prompts = st.button(
        "Wygeneruj pomysły",
        use_container_width=False
    )

st.divider()





# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    #info
    
    st.caption("ℹ️ Panel ustawień")

    st.info(
        """
        1. Wpisz motyw, wybierz poziom/styl

        2. Wygeneruj pomysły

        3. Zaznacz

        4. Wygeneruj i pobierz kolorowanki
        """
    )

   

    st.divider()
    # Koszty
    st.subheader("💰 Koszty")

    st.metric(
        "Koszt sesji",
        f"${st.session_state.total_cost:.4f}"
    )

    st.metric(
    "Ostatnie zapytanie",
    f"${st.session_state.last_request_cost:.6f}"
    )

    st.divider()

    # Historia
    if st.session_state.get("user") and st.session_state.get("history"):

        history_option = st.selectbox(
            "📚 Historia Wyszukiwania",
            ["Wszystko"] +
            [
                f"{i}|{item.get('theme', 'brak')}"
                for i, item in enumerate(st.session_state.history)
            ]
        )

    else:
        st.info("Zaloguj się, aby zobaczyć historię")
        history_option = "Wszystko"

# ---------------------------------------------------
# STYLE i poziom KOLOROWANEK
# ---------------------------------------------------

level_prompts = {
    "🧒 Dzieci": """
Very simple coloring book style.
Big shapes.
Very thick outlines.
Minimal details.
Easy for children aged 3-6.
""",


    "🧑 Starsze": """
Detailed coloring book page.
Many interesting elements and objects.
Rich scene composition.
Clear black outlines.
More details in characters, clothing, nature and background.
Suitable for children aged 8-12.
Fun and engaging.
Not too complex.
""",

    "🧘 Dorośli": """
Highly detailed coloring book page.
Intricate patterns.
Complex composition.
Many small details.
Professional adult coloring book style.
Relaxing and artistic.
Black and white line art.
"""
}   


style_prompts = {

    "🎭 Cartoon": """
Cartoon coloring book style.
Friendly characters.
Fun and playful.
""",

    "🌸 Kawaii": """
Cute kawaii style.
Big eyes.
Adorable characters.
Japanese coloring book style.
""",

    "🐉 Fantasy": """
Fantasy coloring book.
Dragons.
Magic.
Epic adventure.
Fantasy world.
""",

    "🦖 Realistic": """
Realistic coloring book.
Natural proportions.
Educational illustration style.
Detailed realistic objects.
""",

    "🧘 Mandala": """
Mandala coloring book.
Decorative patterns.
Symmetrical elements.
Relaxing and meditative.
"""
}

# ---------------------------------------------------
# GENEROWANIE POMYSŁÓW
# ---------------------------------------------------

if generate_prompts and theme:
    st.session_state.selected_prompts = []

    with st.spinner("Tworzę propozycje..."):

        response = openai_client.responses.create(
            model="gpt-5-mini",
            input=f"""
Wygeneruj 15 krótkich pomysłów na kolorowanki.

Motyw:
{theme}

Zwróć TYLKO poprawny JSON array stringów.
    Bez komentarzy.
    Bez markdown.
    Bez dodatkowego tekstu.

    Format:
    ["a", "b", "c"]
    """
    )

        try:

            st.session_state.prompts = json.loads(
                response.output_text
            )

            usage = getattr(response, "usage", None)
            if usage:
                
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens

                

                INPUT_PRICE = 0.00000025
                OUTPUT_PRICE = 0.00000200

                cost = (
                    input_tokens * INPUT_PRICE +
                    output_tokens * OUTPUT_PRICE
                )

                st.session_state.last_request_cost = cost
                st.session_state.total_cost += cost
                

        except json.JSONDecodeError:
            st.error("Model zwrócił niepoprawny JSON.")

        except Exception as e:
            st.error(f"Błąd: {e}")


# ---------------------------------------------------
# WYBÓR KOLOROWANEK
# ---------------------------------------------------

selected = []

if st.session_state.prompts:

    st.header("Wybierz kolorowanki")

    cols = st.columns(3)

    for idx, prompt in enumerate(st.session_state.prompts):

        with cols[idx % 3]:

            checked = st.checkbox(prompt, key=f"cb_{idx}")

            if checked:
                selected.append(prompt)

if "last_selected" not in st.session_state:
    st.session_state.last_selected = []

# if sorted(selected) != sorted(st.session_state.last_selected):
#     st.session_state.generated_images = []


#st.session_state.last_selected = selected

# ---------------------------------------------------
# GENEROWANIE OBRAZÓW
# ---------------------------------------------------

if selected:

    if st.button(
        "🎨 Generuj kolorowanki",
        use_container_width=False
    ):  
        
        
        # session_id = str(uuid.uuid4())
        # session_folder = f"history/{session_id}"
        # os.makedirs(session_folder, exist_ok=True)

        session_images = []
        
        

        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        request_cost = 0.0
        IMAGE_COST = 0.04

       

        # with st.spinner("Generuję kolorowanki..."):

        for i, idea in enumerate(selected):

             # CHECK DUPLIKATÓW
            if idea in st.session_state.generated_titles:
                continue

            try:
                with st.spinner(f"Generuję: {idea}"):

                    image_prompt = f"""
Coloring book page.

Theme:
{idea}

Difficulty:
{level_prompts[level]}

Style:
{style_prompts[style]}

Black and white line art.
Printable.
White background.
No grayscale.
No shading.
High quality.
"""



                    image = openai_client.images.generate(
                        model="gpt-image-1",
                        prompt=image_prompt,
                        size="1024x1536"
                    )

                    request_cost += IMAGE_COST
                    #base64
                    
                    image_bytes = base64.b64decode(image.data[0].b64_json)

                    file_name = f"{uuid.uuid4()}.png"

                    supabase.storage.from_("images").upload(
                        file_name,
                        image_bytes,
                        file_options={"content-type": "image/png"}
                    )

                    public_url = supabase.storage.from_("images").get_public_url(file_name)

                    image_data = {
                        "id": str(uuid.uuid4()),
                        "title": idea,
                        "url": public_url
                    }



                    st.session_state.generated_images.append(image_data)
                    session_images.append(image_data.copy())

                    st.session_state.generated_titles.add(idea)

                    MAX_IMAGES = 100

                    if len(st.session_state.generated_images) > MAX_IMAGES:
                        st.session_state.generated_images = (
                            st.session_state.generated_images[-MAX_IMAGES:]
                        )

            except Exception as e:
                st.error(f"Błąd generowania obrazu: {e}")
                continue

            # aktualizacja progress baru
            progress_bar.progress((i + 1) / len(selected))

        progress_placeholder.empty()

        st.session_state.last_request_cost = request_cost
        st.session_state.total_cost += request_cost

        

        if session_images:

            history_item = {
                "user_id": st.session_state.user.id,
                "theme": theme,
                "level": level,
                "style": style,
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "images": session_images
            }

            try:
                response = (
                    supabase.table("history")
                    .insert(history_item)
                    .execute()
                )

                # zapisz ID zwrócone przez Supabase
                history_item["id"] = response.data[0]["id"]

                # dopiero teraz dodaj do Session State
                st.session_state.history.append(history_item)

            except Exception as e:
                st.error(f"Błąd zapisu historii: {e}")


            # MAX_HISTORY = 15

            # if len(st.session_state.history) > MAX_HISTORY:
            #     st.session_state.history = st.session_state.history[-MAX_HISTORY:]

            #save_history(st.session_state.history)

            
        st.success("✔ Gotowe")

# ---------------------------------------------------
# GALERIA
# ---------------------------------------------------

if st.session_state.generated_images:

    st.divider()

    st.header("Gotowe kolorowanki")

    cols = st.columns(4)

    for idx, img in enumerate(
        st.session_state.generated_images
    ):

        with cols[idx % 4]:
            

            st.image(
            base64.b64decode(img["base64"]),
            use_container_width=True
            )

            st.caption(img["title"])

            

            if st.button("❌", key=f"del_{img['id']}_main"):

                # usuń z aktualnych obrazów
                st.session_state.generated_images = [
                    x for x in st.session_state.generated_images
                    if x["id"] != img["id"]
                ]

                # znajdź i zaktualizuj tylko jedną sesję
                for session in st.session_state.history:

                    # sprawdzamy czy obraz jest w tej sesji
                    if any(x["id"] == img["id"] for x in session["images"]):

                        # usuń obraz z sesji
                        session["images"] = [
                            x for x in session["images"]
                            if x["id"] != img["id"]
                        ]

                        # jeśli sesja pusta -> usuń z bazy
                        if len(session["images"]) == 0:

                            supabase.table("history") \
                                .delete() \
                                .eq("id", session["id"]) \
                                .execute()

                        else:

                            supabase.table("history") \
                                .update({"images": session["images"]}) \
                                .eq("id", session["id"]) \
                                .execute()

                        break  # <- WAŻNE: kończymy po znalezieniu

                # usuń tytuł
                st.session_state.generated_titles.discard(img["title"])

                st.rerun()

            image_bytes = base64.b64decode(
            img["base64"]
            )

            st.download_button(
                "⬇ Pobierz PNG",
                data=image_bytes,
                file_name=f"{img['id']}.png",
                mime="image/png",
                use_container_width=True
            )

# Galeria Historia



st.divider()

st.header("Historia Wyszukiwania")

if history_option == "Wszystko":
    selected_history = None
else:
    idx = int(history_option.split("|")[0])
    selected_history = st.session_state.history[idx]

if selected_history:

    all_images = selected_history["images"]

else:

    all_images = []
    for history_item in reversed(st.session_state.history):
        all_images.extend(history_item["images"])


if st.button(
    "🗑️ Usuń całą historię",
    type="secondary",
    use_container_width=False
):
    st.session_state.confirm_delete_history = True
    st.rerun()
    


if st.session_state.get("confirm_delete_history", False):

    st.warning(
        "⚠️ Czy na pewno chcesz usunąć CAŁĄ historię?" 
        " Operacji nie można cofnąć."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("✅ Tak"):

            #if os.path.exists("history"):
                #shutil.rmtree("history")

            #os.makedirs("history", exist_ok=True)

            supabase.table("history").delete().neq("id", 0).execute()

            st.session_state.history = []
            st.session_state.generated_images = []
            #save_history([])
            st.session_state.generated_titles = set()
            st.session_state.confirm_delete_history = False

            st.success("Historia została usunięta.")
            st.rerun()

    with col2:

        if st.button("❌ Anuluj"):

            st.session_state.confirm_delete_history = False
            st.rerun()
   



# pokazujemy jako jedna galeria
cols = st.columns(4)

for idx, img in enumerate(all_images):

    with cols[idx % 4]:

        # if os.path.exists(img["file"]):

            st.image(
                base64.b64decode(img["base64"]),
                caption=img["title"],
                use_container_width=True
            )
            image_bytes = base64.b64decode(
                img["base64"]
            )

        #     with open(img["file"], "rb") as f:
        #         image_bytes = base64.b64decode(
        #         img["base64"]
        #         )

            st.download_button(
                "⬇ Pobierz",
                data=image_bytes,
                file_name=f"{img['id']}.png",
                mime="image/png",
                use_container_width=True,
                key=f"hist_dl_{img['id']}"
            )
        
#st.write(st.session_state.history)

