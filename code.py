import json
import time
import pandas as pd
from kaggle_secrets import UserSecretsClient
from google import genai
from google.genai import types
from google.genai.errors import APIError


def get_valid_number(prompt_text, num_type=int, min_val=None, max_val=None):

    while True:
        try:
            value = num_type(input(prompt_text).strip())

            if min_val is not None and value < min_val:
                print(f"❌ Value must be >= {min_val}")
                continue

            if max_val is not None and value > max_val:
                print(f"❌ Value must be <= {max_val}")
                continue

            return value

        except ValueError:
            print("❌ Please enter valid numeric input.")


def normalize_gender():

    while True:

        val = input(
            "⚧ Enter Gender (M/F/Other): "
        ).strip().upper()

        male_values = ["M", "MALE", "BOY"]
        female_values = ["F", "FEMALE", "GIRL"]
        other_values = ["OTHER", "OTHERS", "O"]

        if val in male_values:
            return "MALE"

        elif val in female_values:
            return "FEMALE"

        elif val in other_values:
            return "OTHER"

        else:
            print("❌ Invalid gender entered.")


def get_valid_category():

    valid_categories = [
        "GENERAL",
        "OBC",
        "SC/ST"
    ]

    while True:

        category = input(
            "👥 Enter Category (General/OBC/SC/ST): "
        ).strip().upper()

        if category in ["SC", "ST", "SCST"]:
            category = "SC/ST"

        if category in valid_categories:
            return category

        print(
            "❌ Invalid category. "
            "Please enter General, OBC, SC, or ST."
        )


def print_line():
    print("═" * 70)


def main():

    try:

        user_secrets = UserSecretsClient()

        gemini_key = user_secrets.get_secret(
            "GEMINI_API_KEY"
        )

        if not gemini_key:
            print("❌ API Key missing in Kaggle Secrets.")
            return

        client = genai.Client(api_key=gemini_key)

        print("✅ SCHOLAR_PATH-AI Connected")

    except Exception as e:

        print(f"❌ Gemini Setup Error: {e}")
        return

    scholarship_data = {

        "Scheme_ID": [
            "SCH-001",
            "SCH-002",
            "SCH-003",
            "SCH-004",
            "SCH-005",
            "SCH-006"
        ],

        "Scheme_Name": [
            "Post-Matric Scholarship for OBC Students",
            "National Merit-cum-Means Scholarship",
            "PM-USP Technical Education Scholarship",
            "Utkrishth Uchch Shiksha Protsahan",
            "SC/ST Excellence Scholarship",
            "Women in Technology Merit Scholarship"
        ],

        "Allowed_State": [
            "Uttarakhand",
            "ALL",
            "ALL",
            "Uttarakhand",
            "ALL",
            "ALL"
        ],

        "Allowed_Category": [
            "OBC",
            "GENERAL",
            "OBC",
            "GENERAL",
            "SC/ST",
            "ALL"
        ],

        "Max_Annual_Income_Limit": [
            250000,
            600000,
            450000,
            300000,
            350000,
            1000000
        ],

        "Min_CGPA_Required": [
            6.0,
            8.5,
            6.5,
            8.0,
            5.5,
            8.5
        ],

        "Financial_Benefit": [
            50000,
            75000,
            100000,
            40000,
            120000,
            150000
        ],

        "Allowed_sex": [
            "MALE",
            "ALL",
            "ALL",
            "ALL",
            "ALL",
            "FEMALE"
        ],

        "Official_Portal_Link": [
            "https://scholarships.gov.in",
            "https://scholarships.gov.in",
            "https://scholarships.gov.in",
            "https://scholarships.gov.in",
            "https://scholarships.gov.in",
            "https://www.aicte-india.org"
        ]
    }

    try:

        df_schemes = pd.DataFrame(
            scholarship_data
        )

        print("✅ Scholarship database loaded")

    except Exception as e:

        print(f"❌ DataFrame Error: {e}")
        return

    print("\n")
    print_line()
    print("🎓 SCHOLARSPATH AI")
    print_line()

    input_state = input(
        "📍 Enter Home State: "
    ).strip().title()

    input_category = get_valid_category()

    input_income = get_valid_number(
        "💰 Enter Annual Family Income ₹: ",
        int,
        0
    )

    input_cgpa = get_valid_number(
        "📈 Enter Current CGPA (0-10): ",
        float,
        0,
        10
    )

    input_gender = normalize_gender()

    user_profile = {

        "state": input_state,

        "category": input_category,

        "income": input_income,

        "cgpa": input_cgpa,

        "sex": input_gender
    }

    print("\n⏳ Matching scholarships...")

    state_match = (

        (
            df_schemes['Allowed_State']
            .str.lower()
            ==
            user_profile['state'].lower()
        )

        |

        (
            df_schemes['Allowed_State']
            .str.upper()
            ==
            'ALL'
        )
    )

    category_match = (

        (
            df_schemes['Allowed_Category']
            .str.upper()
            ==
            user_profile['category']
        )

        |

        (
            df_schemes['Allowed_Category']
            .str.upper()
            ==
            'ALL'
        )
    )

    income_match = (

        df_schemes[
            'Max_Annual_Income_Limit'
        ]

        >=

        user_profile['income']
    )

    cgpa_match = (

        df_schemes[
            'Min_CGPA_Required'
        ]

        <=

        user_profile['cgpa']
    )

    sex_match = (

        (
            df_schemes['Allowed_sex']
            .str.upper()
            ==
            user_profile['sex']
        )

        |

        (
            df_schemes['Allowed_sex']
            .str.upper()
            ==
            'ALL'
        )
    )

    matched_rows = df_schemes[
        state_match
        &
        category_match
        &
        income_match
        &
        cgpa_match
        &
        sex_match
    ]

    if not matched_rows.empty:

        matched_rows = matched_rows.copy()

        matched_rows["Score"] = (

            (
                matched_rows[
                    "Financial_Benefit"
                ] / 1000
            )

            +

            (
                10
                -
                abs(
                    matched_rows[
                        "Min_CGPA_Required"
                    ]
                    -
                    user_profile["cgpa"]
                )
            )
        )

        matched_rows = matched_rows.sort_values(
            by="Score",
            ascending=False
        )

    matched_list = matched_rows.to_dict(
        orient="records"
    )

    print(
        f"✅ Found "
        f"{len(matched_list)} "
        f"matching scholarships"
    )

    # =================================================
    # AI GUIDANCE GENERATION
    # =================================================

    if len(matched_list) > 0:

        print("\n🧠 Generating AI Guidance...\n")

        scholarship_text = ""

        unique_links = set()

        for idx, item in enumerate(
            matched_list,
            start=1
        ):

            scholarship_text += f"""

{idx}. {item["Scheme_Name"]}

Benefit Amount:
₹{item["Financial_Benefit"]}

Official Website:
{item["Official_Portal_Link"]}

"""

            unique_links.add(
                item["Official_Portal_Link"]
            )

        # =============================================
        # SYSTEM INSTRUCTION
        # =============================================

        system_instruction = """
You are ScholarsPath AI.

Your responsibilities:
- Guide students professionally.
- Give positive and encouraging feedback.
- Never insult or discriminate based on category,
  gender, income, or academic background.
- Explain scholarship opportunities clearly.
- Help avoid document rejection.

IMPORTANT:
- Do invent official and correct scholarship links.
- Do NOT rewrite URLs.
- Keep response concise and beautiful.
"""

        prompt = f"""
STUDENT PROFILE:
{json.dumps(user_profile, indent=2)}

ELIGIBLE SCHOLARSHIPS:
{scholarship_text}

TASKS:

1. Give positive profile feedback.
2. Write motivational introduction.
3. Create required document checklist.
4. Give 3 expert tips.
5. Mention scholarship benefits.
6. Mention students should always verify
   latest deadlines from official portals.

Use attractive formatting.
Keep response under 300 words.
"""

        response = None

        for attempt in range(3):

            try:

                response = client.models.generate_content(

                    model="gemini-2.5-flash",

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        temperature=0.3,

                        system_instruction=system_instruction
                    )
                )

                break

            except APIError as api_err:

                print(
                    f"⚠️ API Error "
                    f"(Attempt {attempt + 1}): "
                    f"{api_err}"
                )

                time.sleep(2)

            except Exception as e:

                print(
                    f"⚠️ Unexpected Error: {e}"
                )

                time.sleep(2)

        if response and response.text:

            print("\n")
            print_line()
            print("📜 PERSONALIZED SCHOLARSHIP ROADMAP")
            print_line()

            print(response.text)

            print("\n")
            print_line()
            print("🔗 VERIFIED OFFICIAL SCHOLARSHIP LINKS")
            print_line()

            for idx, item in enumerate(
                matched_list,
                start=1
            ):

                print(
                    f"{idx}. "
                    f"{item['Scheme_Name']}"
                )

                print(
                    f"👉 "
                    f"{item['Official_Portal_Link']}"
                )

                print()

            print_line()

            print(
                "✅ Always verify latest "
                "application deadlines "
                "on official portals."
            )

        else:

            print(
                "\n❌ Failed to generate AI response."
            )

    else:

        print(
            "\n❌ No scholarship schemes "
            "matched your profile."
        )


if __name__ == "__main__":
    main()
