from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import json
import time
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
from datetime import datetime
from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager, register_function
import autogen
from typing import Optional, Literal, List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
# from langchain.output_parsers import PydanticOutputParser
# from langchain_community.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import PydanticOutputParser

import time
import ast
import re
import base64


from tools_manager import (
    get_top_alternative_suppliers,
    find_alternate_suppliers_by_cost,
    find_suppliers_for_due_date, list_expired_inventory,
    rank_suppliers_by_leadtime_and_moq,
    calculate_transit_time,
    get_open_po_data,
    expedite_po_by_cost,
    expedite_po_by_lead,
    get_avg_lead_time,
    update_import_duties,
    get_best_suppliers,
    get_best_suppliers_by_lead_cost,
    analyze_po_requirements,
    get_delayed_shipments_to_east_coast,
    analyze_stockout_risk_by_dc,
    recommend_container_rerouting,
    calculate_cost_benefit_analysis,
    calculate_financial_impact_and_recommendation,
    extract_invoice_details,
    get_po_grn_details,
    generate_alphanumeric_string,
    clear_pdfs,
    calculate_eta_from_files,
    analysed_pr_details,
    send_reminder_email_to_approver
)

app = FastAPI(title="Supplier Analysis API")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_usd_currency(value):
    """
    Converts a numeric value (int or float) to a string with commas as thousands separators.
    """
    try:
        # If it's a float, format with two decimal places; otherwise just add commas
        if isinstance(value, float):
            return f"{value:,.2f}"
        else:
            return f"{value:,}"
    except Exception as e:
        return str(e)


def email_sending_tool(
        po_mail_subject: str,
        supplier: str,
        shipping: str,
        item: str,
        quantity: int,
        cost: float,
        supplier_eta_date: str,

):
    try:
        # Create the email message
        current_date = datetime.now().strftime('%d-%m-%Y ( at %H:%M )')
        html_body = f"""
        <!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    /* Reset and base */
    body {{
      margin: 0;
      padding: 0;
      background-color: #F9FAFB;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #1F2937;
      line-height: 1.5;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    /* Container to center content */
    .container {{
      max-width: 600px;
      margin: 0 auto;
      padding: 24px;
    }}

    /* Card with subtle shadow and rounded corners */
    .card {{
      background-color: #FFFFFF;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(31, 41, 55, 0.1);
      overflow: hidden;
    }}

    /* Accent bar at top of card */
    .accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, #2563EB, #8B5CF6);
    }}

    /* Header inside card */
    .card-header {{
      padding: 24px;
    }}

    .card-header h2 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: #4F46E5;
      /* Purple */
    }}

    .card-header p.date {{
      margin-top: 4px;
      font-size: 0.875rem;
      color: #6B7280;
    }}

    /* Body content */
    .card-body {{
      padding: 0 24px 24px;
    }}

    .card-body p {{
      margin: 16px 0;
      font-size: 1rem;
      color: #374151;
    }}

    /* Table styling */
    .details-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
    }}

    .details-table th,
    .details-table td {{
      padding: 12px 16px;
      text-align: left;
    }}

    .details-table thead th {{
      background-color: #E0E7FF;
      /* Light indigo */
      color: #4F46E5;
      /* Purple */
      font-weight: 600;
    }}

    .details-table tbody tr {{
      border-bottom: 1px solid #E5E7EB;
    }}

    .details-table tbody tr:nth-child(even) {{
      background-color: #F3F4F6;
    }}

    .details-table td {{
      color: #374151;
      font-weight: 500;
    }}

    /* Footer */
    .footer {{
      font-size: 0.75rem;
      color: #9CA3AF;
      text-align: center;
      margin: 16px 0;
    }}

    /* Responsive adjustments */
    @media (max-width: 600px) {{
      .container {{
        padding: 16px;
      }}

      .card-header h2 {{
        font-size: 1.25rem;
      }}

      .details-table th,
      .details-table td {{
        padding: 8px 12px;
      }}
    }}
  </style>
</head>

<body>
  <div class="container">
    <div class="card">
      <div class="accent-bar"></div>
      <div class="card-header">
        <h2>New Purchase Order Created by OptiBuy</h2>
        <p class="date"><strong>Date:</strong> {current_date}</p>
        <p>Authorized by Procurement Mananger: <b>Priya Sharma</b></p>
      </div>
      <div class="card-body">
        <p>Dear Procurement Team,</p>
        <p>OptiBuy has created a new Purchase Order. Below are the details:</p>
        <table class="details-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Supplier</td>
              <td>{supplier}</td>
            </tr>
            <tr>
              <td>Shipping Modality</td>
              <td>{shipping}</td>
            </tr>
            <tr>
              <td>Item</td>
              <td>{item}</td>
            </tr>
            <tr>
              <td>Quantity</td>
              <td>{quantity}</td>
            </tr>
            <tr>
              <td>Total Cost (USD)</td>
              <td>$ {to_usd_currency(cost)}</td>
            </tr>
            <tr>
              <td>Supplier ETA</td>
              <td>{supplier_eta_date}</td>
            </tr>
          </tbody>
        </table>
        <p style="color:#4F46E5;">For further assistance, please reference this PO number in any correspondence with the procurement manager:
          Priya Sharma.</p>
        <p class="footer">This is an automated email sent by ProcureWise AI. Do not reply directly to this email.</p>
      </div>
    </div>
  </div>
</body>

</html>
        """

        # Email configuration
        # Replace with your verified sender email
        sender_email = "santosh.selvam@gmail.com"
        recipient_email = "optibuy.procurewiseai@gmail.com"  # Replace with recipient email
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
  # Load from environment variable
        # Create the SendGrid email object
        message = Mail(
            from_email=sender_email,
            to_emails=recipient_email,
            subject=f"New Purchase Order Created - {po_mail_subject}",
            html_content=html_body
        )

        print(type(message))

        # Send the email using SendGrid API
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)

        purchase_order_summary = f"""Purchase Order created and sent successfully. Details:

        
- Supplier: {supplier}
- Shipping: {shipping}
- Item: {item}
- Quantity: {quantity}
- Cost: $ {to_usd_currency(cost)}
- Lead Time: {supplier_eta_date}

        """

        return f"{purchase_order_summary}\n\nEmail sent successfully to {recipient_email}!"

    except Exception as e:
        return f"Failed to send email: {str(e)}"


def email_sending_tool_generic(
        po_mail_subject: str,
        html_body: str,
        post_sending_message: str
):
    """
    Sends an HTML-formatted email using the SendGrid API.

    Parameters:
        po_mail_subject (str): Subject line of the email.
        html_body (str): HTML content for the email body.
        post_sending_message (str): Summary message to return after sending.

    Returns:
        str: Success or failure message.
    """
    try:
        current_date = datetime.now().strftime('%d-%m-%Y ( at %H:%M )')

        sender_email = "santosh.selvam@gmail.com"
        recipient_email = "optibuy.procurewiseai@gmail.com"
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

        message = Mail(
            from_email=sender_email,
            to_emails=recipient_email,
            subject=f"{po_mail_subject}",
            html_content=html_body.replace("{CURRENT_DATE}", current_date)
        )

        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)

        return f"{post_sending_message}\n\nEmail sent successfully to {recipient_email}!"

    except Exception as e:
        return f"Failed to send email: {str(e)}"


# === 0. Load environment ===
load_dotenv()
# Removed Google API key - using OpenAI instead
openai_api_key = os.getenv("OPENAI_API_KEY")

config_list_gpt_4o_mini = [{
    "model": "gpt-4o",
    "api_key": openai_api_key
}]


os.environ['AUTOGEN_USE_DOCKER'] = '0'


class SupplierQuery(BaseModel):
    query: str
    chat_summary: str
    pdfs: Optional[List] = None


class PanamaCanalQuery(BaseModel):
    affected_dc: str = "DC3"  # Default to DC3 which typically has highest-value electronics
    delay_days: int = 15
    # "delayed_shipments", "stockout_risk", "rerouting", "cost_benefit", "full"
    analysis_type: str = "full"


# === 3. Define structured output model ===
class FunctionCall(BaseModel):
    function_name: Literal[
        "expedite_supply_workflow",
        "tariff_impact_workflow",
        "route_disruption_workflow",
        "draft_po_workflow",
        "send_email_workflow",
        "panama_canal_workflow",
        "extract_invoice_details_workflow",
        "seek_supplier_correction_email_workflow",
        "read_pr_emails_workflow",
        "send_pr_to_approver_email_workflow",
        "pr_pending_workflow",
        "send_pr_reminder_email_workflow",
        "calculate_pr_schedule_changes_workflow"
    ]
    args: dict


# === 4. Setup LangChain prompt + parser ===
parser = PydanticOutputParser(pydantic_object=FunctionCall)

prompt = PromptTemplate(
    template=(
        "You have access to the following functions:\n"
        "- expedite_supply_workflow()\n"
        "- tariff_impact_workflow()\n"
        "- route_disruption_workflow()\n"
        "- draft_po_workflow()\n"
        "- send_email_workflow()\n"
        "- panama_canal_workflow()\n"
        "- extract_invoice_details_workflow()\n"
        "- seek_supplier_correction_email_workflow()\n"
        "- read_pr_emails_workflow()\n"
        "- send_pr_to_approver_email_workflow()\n"
        "- pr_pending_workflow()\n"
        "- send_pr_reminder_email_workflow()\n"
        "- calculate_pr_schedule_changes_workflow()\n"

        """
        Note : Do not change your answer frequently.
        Some Examples:
        Q: Suggest options to expedite existing open purchase order (PO-103916) with lead time impact
        
        Select: expedite_supply_workflow()

        Q: Show me alternate strategy for above purchase order

        Select: expedite_supply_workflow()

        Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

        Select: tariff_impact_workflow()

        Q: I forgot to mention that there is news about a trade deal between US-Japan which will come into effect after 5 days from now and will make tariff on ITM-002 to 0 . Does this change our latest scenario?

        Select: tariff_impact_workflow()

        Q: Just Inquired from supplier, there was a delay and PO104007 material will get delivered by tomorrow. Reason for the delay is due to heightened naval tensions in the South China Sea, following a disputed military exercise and temporary maritime restrictions imposed by Chinese authorities, currently shipping lane route from China to US is taking longer route which will increase normal transit time by 15 days. Find out which other orders could be impacted.

        Select: route_disruption_workflow()

        Q: Yes, please create an emergency PO draft with Supplier O for ITM-002.

        Select: draft_po_workflow()

        Q: Please draft a PO for Supplier O for ITM-004

        Select: draft_po_workflow()

        Q: yes, I authorize the details, please send the email.

        Select: send_email_workflow()

        Q: Yes, please send the mail

        Select: send_email_workflow()

        Q: Go ahead I confirm these details

        Select: send_email_workflow()

        Q: Match PO-79073, attached invoice and GRN100100172 required information for correctness before release of payment.
        
        Select: extract_invoice_details_workflow()

        Q: Yes, go ahead and seek clarification on inaccuracies in the invoice
        
        Select: seek_supplier_correction_email_workflow()

        Q: Check email for PR Request
        
        Select: read_pr_emails_workflow()

        Q: Yes, please release the PR with the above details
        
        Select: send_pr_to_approver_email_workflow()

        Q: Track status of PRs: PR-XXXXX1, PR-XXXXX2, PR-XXXXX3
        
        Select: pr_pending_workflow()

        Q: Yes, go ahead and send a reminder.
        
        Select: send_pr_reminder_email_workflow()
        
        Q: Yes, go ahead and send a reminder [for PR].
        
        Select: send_pr_reminder_email_workflow()
        
        Q: Send reminder email for PR-103101
        
        Select: send_pr_reminder_email_workflow()

        Q: Check schedule changes for this PR
        
        Select: calculate_pr_schedule_changes_workflow()
        
        Q: Due to Panama Canal slowdown, 15-day delays are affecting shipments to East Coast ports. Analyze shipments heading to DC1 and provide cost-benefit analysis for container rerouting.

        Select: panama_canal_workflow()
        
        Q: Panama Canal delays are impacting our East Coast deliveries. Can you analyze the impact on DC2 and recommend rerouting options?

        Select: panama_canal_workflow()
        
        Q: I heard about Panama Canal work slowdown causing delays to New York port. Check which shipments are affected and if we should reroute containers.

        Select: panama_canal_workflow()
        
        Q: Alright, please update the PO and inform the travel planners to reroute the shipment.
        
        Select: panama_canal_workflow()
        
        Q: Kindly update the PO for the Panama Canal rerouting.
        
        Select: panama_canal_workflow()
        
        Q: Go ahead with the rerouting. Update the PO.
        
        Select: panama_canal_workflow()
        
        Q: Proceed with the container rerouting and notify transport planners.
        
        Select: panama_canal_workflow()
        """
        "Based on the user request, choose the appropriate function and provide its name and arguments as JSON.\n"
        "{format_instructions}\n\n"
        "User: {user_query}"
    ),
    input_variables=["format_instructions", "user_query"]
)

prompt_chain = prompt.partial(
    format_instructions=parser.get_format_instructions()
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=openai_api_key
)

pipeline = prompt_chain | llm | parser

# === 5. Function to handle user query ===


def handle_user_query(orchestration_mssg, query, chat_summary):
    try:
        call = pipeline.invoke({"user_query": query})
        fn = function_registry.get(call.function_name)
        if fn:
            return fn(orchestration_mssg, query, chat_summary)
        else:
            return f"Unknown function: {call.function_name}"
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"


@app.post("/supplier-analysis")
def supplier_analysis(request: SupplierQuery):

    try:
        try:
            request_list = request.pdfs

            if request_list:
                for request_element in request_list:
                    pdf_bytes = base64.b64decode(request_element["data"])
                    random_pdf_name = generate_alphanumeric_string(12)
                    with open(f"./updated_docs/pdf_store/{random_pdf_name}.pdf", "wb") as f:
                        f.write(pdf_bytes)
            chat_summary = request.chat_summary
            print("CHAT SUMMARY:\n`"+chat_summary+"`")
        except Exception as err:
            print("ERROR:\n\n")
            print(err)
            try:
                chat_summary = request.chat_summary
                print("CHAT SUMMARY:\n`"+chat_summary+"`")

            except:
                chat_summary = None
                print("ERROR:\n\n")
                print(err)

        result = handle_user_query([], request.query, chat_summary)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            clear_pdfs()
        except Exception as cleanup_err:
            print("Failed to clear PDFs:", cleanup_err)


def save_pr_email_to_json(email_data: dict):
    """
    Save processed PR email to JSON file.
    Creates the file if it doesn't exist, or appends to existing file.
    """
    json_path = "./updated_docs/pr_folders/pr_extractions/pr_ext.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    try:
        # Try to read existing data
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        else:
            existing_data = []

        # Add new email data at the beginning (most recent first)
        existing_data.insert(0, email_data)

        # Keep only last 50 emails to prevent file from growing too large
        existing_data = existing_data[:50]

        # Write back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Error saving PR email to JSON: {e}")
        return False


def process_incoming_email(subject: str, body: str, from_email: str, to_email: str, date: str = None):
    """
    Process incoming email and extract PR-related information.
    Returns a structured dictionary with email details.
    """
    if date is None:
        date = datetime.now().isoformat()

    # Clean HTML from body if present
    import re
    # Remove HTML tags
    clean_body = re.sub(r'<[^>]+>', '', body)
    # Decode HTML entities
    clean_body = clean_body.replace('&nbsp;', ' ').replace(
        '&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Remove extra whitespace
    clean_body = ' '.join(clean_body.split())

    email_data = {
        "subject": subject,
        "body": clean_body,
        "html_body": body,  # Keep original HTML for reference
        "from": from_email,
        "to": to_email,
        "date": date,
        "processed_at": datetime.now().isoformat()
    }

    return email_data


def fetch_pr_emails():
    """
    Fetch PR emails from the JSON file.
    Returns formatted string with email details, or error message if no emails found.
    """
    json_path = "./updated_docs/pr_folders/pr_extractions/pr_ext.json"

    try:
        if not os.path.exists(json_path):
            return "No PR emails have been received yet. Emails will appear here once they are received via SendGrid webhook."

        with open(json_path, 'r', encoding='utf-8') as f:
            text = json.load(f)

        if not text:
            return "No PR emails found in the system."

        # Handle both list and single dict formats
        if isinstance(text, list):
            emails = text
        else:
            emails = [text]

        if not emails:
            return "No PR emails found in the system."

        # Format the most recent email (first in list)
        latest_email = emails[0]

        # Extract clean body (remove HTML if present)
        body = latest_email.get('body', latest_email.get('html_body', ''))
        if '<div dir=' in body:
            body = body.split("<div dir=")[0]

        return_string = f"""
    # Email received from plant official to Procurement Team:

    ## Subject: {latest_email.get('subject', 'No Subject')}
    
    ## From: {latest_email.get('from', 'Unknown Sender')}
    
    ## Date: {latest_email.get('date', 'Unknown Date')}
    
    ## Body:

    {body}

    """

        return return_string

    except json.JSONDecodeError as e:
        return f"Error reading PR email data: Invalid JSON format. {str(e)}"
    except Exception as e:
        return f"Error fetching PR emails: {str(e)}"


def send_email_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        email_sending_agent = ConversableAgent(
            "email_sending_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            You are **email\_sending\_agent**.

Your task is to read the user's last message, extract Purchase Order details, and draft a PO table. Follow these rules exactly:

1. **Table Format**

   * Use Markdown to create a table with these columns:

     | Field        | Details              |
     | ------------ | -------------------- |
     | Supplier     | `<Name> (Code)`      |
     | Shipping     | `<Modality>`         |
     | Item         | `<Item Description>` |
     | Quantity     | `<Quantity>`         |
     | Total Cost   | `<Amount>`           |
     | Supplier ETA | `<DD/MM/YYYY>`       |

2. **Extraction**

   * **Supplier**: name and code as provided by the user.
   * **Shipping**: default to "Air Shipping" if not specified.
   * **Supplier ETA**: default to "24/06/2025" (DD/MM/YYYY) if not given.

3. **Email Sending**

   * Only invoke **email_sending_tool** after the user explicitly authorizes sending the email.
   * If the user does not confirm, do **not** call the tool; simply return the PO table.

4. **Output**

   * Present only the PO table in Markdown.
   * If awaiting authorization, include a brief confirmation request instead of the table.

---

**Example** (after extracting details):

| Field        | Details                 |
| ------------ | ----------------------- |
| Supplier     | Acme Corp (AC123)       |
| Shipping     | Air Shipping            |
| Item         | Industrial Pump Model X |
| Quantity     | 10                      |
| Total Cost   | \$5,000                 |
| Supplier ETA | 24/06/2025              |

---

            **IMPORTANT: End your response with "TERMINATE" to properly conclude the workflow.**

            """,
        )

        register_function(
            email_sending_tool,
            caller=email_sending_agent,
            executor=email_sending_agent,
            name="email_sending_tool",
            description="Send an email using this tool only if user confirms/authorises you to send the email.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            email_sending_agent
        ]

        transitions_list = {
            you: [email_sending_agent],
            email_sending_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def draft_po_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **p2p_compliance_agent**.
            # Role:
            Study the previous message and draft a Purchase Order table, similar to following table, based on the details you have extracted:
            
            Calculate the total cost: Units requested by the user * Landed Cost per Item 

            Take time, think step by step and then prepare the PO draft.
            
            # Returning Format [Return in Markdown Format]:

                    ---

            
                    ## PO Details:

                    | Field        | Details                |
                    |------------|----------------------|
                    | Supplier   | {{supplier name and Supplier Code}}             |
                    | Shipping  | {{shipping_modality by default take Air Shipping}}             |
                    | Item       | {{item}}             |
                    | Quantity   | {{quantity}}             |
                    | Total Cost       | {{total cost}}             |
                    | Supplier ETA  | {{supplier_eta by default take 24/06/2025}}             |

                    ---

                    ### Confirmation:

                    Shall I proceed with sending the email to the supplier `supplier.company@comp.com` regarding the above purchase order? I'll include you `(priya.sharma@company.com)` and also sync details with the procurement team (main.procurement@company.com) in CC.

                    **IMPORTANT: End your response with "TERMINATE" to properly conclude the workflow.**

        
            """,
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            p2p_compliance_agent
        ]

        transitions_list = {
            you: [p2p_compliance_agent],
            p2p_compliance_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def route_disruption_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **p2p_compliance_agent**.
            # Role:
            Your task is to initiate the **find_open_po_tool** tool that is alloted to you. 
            Extract PO number from user query and pass it to the tool. If PO number is not explicitly mentioned in new query, take PO from  **Chat Summary of Previous Conversation:**
            in the format: 'PO-XXXXXX'
            """,
        )

        strategic_needs_agent = ConversableAgent(
            "strategic_needs_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:

            You are **strategic_needs_agent**.
           
            # Role:
            
            Your job is to run the **affected_routes_tool** tool to check for purchase orders that have been affected.
            Extract PO number from user query and pass it to the tool. If PO number is not explicitly mentioned in new query, take PO from  **Chat Summary of Previous Conversation:**
            in the format: 'PO-XXXXXX'.
            Example: 'PO-104007'
            """,
        )

        supplier_evaluation_agent = ConversableAgent(
            "supplier_evaluation_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **supplier_evaluation_agent**.
            # Role:
            You will be provided with a table/list of top suppliers for a specific item from each supplying country to a specified delivery location.
            Your job is to evaluate suppliers and fetch the best supplier based on total landed costs and lead time.
            Show exact Calculations to get the correct landed cost, this will help you in evaluating the best suppliers.

            Calculate the final landed cost for each supplier based on import duty/tariffs shared to you by **tariff correction agent**.

            Remember:
            - while preparing final landed cost take quantity specified by **strategic_needs_agent** + a little buffer, then round the value to upper limit and then calculate for that quantity.
            - Perform this calculation for every single 'supplier code' including supplier even if in the same country.
            - Now check which supplier has lowest total landed cost and then select best supplier and return the answer in table format.
            - Provide all details about the Recommended Supplier: Supplier Name, Supplier Code, Item Number, Item Name, Unit Cost, Air Shipping Costs, Landed Cost per Item, Supplier ETA [by default: take 24/06/2025]
            - only after this select the best supplier basis total landed cost.
            """,
        )

        logistics_tracker_agent = ConversableAgent(
            "logistics_tracker_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            Your Task is to initiate the **get_import_duties** tool to fetch exact import duties applicable for items. 
            
            # NOTE:

            - YOU ARE ONLY SUPPOSED TO RUN THE **get_import_duties** tool to fetch exact import duty values, do not give any other explanation.
            """,
        )

        supplier_analysis_agent = ConversableAgent(
            "supplier_analysis_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message=f"""
            # Basic Information:
            You are **supplier_analysis_agent**.
            # Role:
            Identify the Item numbers, use the **get_best_suppliers** tool to find best supplier for that specific item numbers.

            Always make use of the **get_best_suppliers** tool to get the most accurate results. Apply shipping_mode to 'air'


            Important Note:

            Only select items that are given to you only by **strategic_needs_agent**, ONLY FOR ITM-002. DO NOT SEARCH FOR ANY OTHER ITEM.

            These are the delivery locations:
            
            {pd.read_csv('./updated_docs/Supplier_data.csv')["Delivery location"].unique()}"
            """,
        )

        register_function(
            get_open_po_data,
            caller=p2p_compliance_agent,
            executor=p2p_compliance_agent,
            name="get_open_po_data",
            description="Use this tool to get Data regarding Open Purchase order based on PO Number",
        )

        register_function(
            get_best_suppliers_by_lead_cost,
            caller=supplier_analysis_agent,
            executor=supplier_analysis_agent,
            name="get_best_suppliers_by_lead_cost",
            description=f"""Use this tool to get top suppliers for a specific item to a delivery location for all supplying countries.\nWrite Item number in this format: ITM-001 or ITM-002. \nThese are the delivery locations: {pd.read_csv('./updated_docs/Supplier_data.csv')["Delivery location"].unique()}""",
        )

        register_function(
            analyze_po_requirements,
            caller=strategic_needs_agent,
            executor=strategic_needs_agent,
            name="analyze_po_requirements",
            description=f"""Use this tool to get details about Purchase Orders that might get disrupted and production orders that might get disrupted, hence providing details on what items can be procured and by when. PO Number must always be provided in this format: PO-XXXXXX.\nExample: 'PO-104007'""",
        )

        register_function(
            update_import_duties,
            caller=logistics_tracker_agent,
            executor=logistics_tracker_agent,
            name="get_import_duties",
            description="""Use this tool to get import duties.""",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Step-by-Step Reasoning

            1. **Interpret** the user's question in full.  
            2. **Decompose** it into atomic sub-questions or metrics to compute (e.g., "What's the average lead time?" , "How did expedited shipping affect costs?").  
            3. **Examine** every table provided—consider relationships, joins, and cross-table comparisons.  
            4. **Perform calculations** (differences, ratios, averages, growth rates, correlations, etc.) to surface insights that aren't immediately visible.  
            5. **Validate** that every conclusion is directly supported by the data; do not introduce unsupported assumptions.

            ---

            ## Some Examples of Thinking:

            Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

            Thought process: Here, user is seeking an alternate supplier for specified Items, they are asking to consider tariffs on China and India, but that doesn't mean that they want suppliers only from China or India, infact they want you to look at all possible suppliers check the overall impact on all suppliers for tariffs and then calculate cost after impact. So a supplier from USA might be best or based on tariff change if the cost comes down then that particular country's supplier might be the best.



            **Q: Suggest options to expedite existing open purchase order (PO-103916) with cost/lead time impact:**

            **Thought Process: Maybe you can look to expedite by switching from sea to air transportation, and hence make joins accordingly for that specific supplier.**
            
            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. Only Study the data provided by User, **strategic_needs_agent** and **supplier_evaluation_agent**. Then prepare you suggestion to the user. 
               Provide exact shipping modality, provide exact supplier code in the table, provide per unit costs and then total cost.


            2. **Markdown Table** [Never Skip: prepare table for suggested supplier and include details like supplier name, supplier code, Shipping: Air, **Total Landed Cost per unit**, Total Landed Cost, Supplier ETA: by default take 24/06/2025]
            - **Supplier Name** and **Supplier Code** Column are mandatory columns. NEVER EVER SKIP THESE COLUMNS.
            - **Total Landed Cost per unit** Column is a mandatory column. NEVER EVER SKIP THIS COLUMN.
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (≥ 100 words)**  
            - Place **immediately after** its corresponding table.  
            - Grounded entirely in the supplied data and your calculations.
            - These Insights should be in bulleted format.
            - Highlight patterns, anomalies, comparisons, and their business or operational implications.  
            - Reference specific table rows or calculated values to justify each point.
            - These insights should be in bulleted format ONLY.

            Repeat the "table → insight" sequence until **every** sub-query has been answered.


            Finally:
            Segue smoothly into Asking if the user has any other questions, maybe you can give some possible follow-up questions like drafting a PO, sending out an email regarding a drafted po.
            Think intelligently and map follow-up questions according to your answer and situation.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > "A meaningful report cannot be generated due to lack of complete data."  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your "table → insight" series in one concise, data-grounded response.

            **IMPORTANT: End your response with "TERMINATE" to properly conclude the analysis workflow.**

            """
        )

        agent_list = [
            you,
            p2p_compliance_agent,
            strategic_needs_agent,
            logistics_tracker_agent,
            supplier_analysis_agent,
            supplier_evaluation_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [p2p_compliance_agent],
            p2p_compliance_agent: [p2p_compliance_agent, strategic_needs_agent],
            strategic_needs_agent: [strategic_needs_agent, supplier_analysis_agent],
            supplier_analysis_agent: [supplier_analysis_agent, logistics_tracker_agent],
            logistics_tracker_agent: [logistics_tracker_agent, supplier_evaluation_agent],
            supplier_evaluation_agent: [optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def tariff_impact_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        supplier_evaluation_agent = ConversableAgent(
            "supplier_evaluation_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **supplier_evaluation_agent**.
            # Role:
            You will be provided with a table/list of top suppliers for a specific item from each supplying country to a specified delivery location.
            Your job is to evaluate suppliers and fetch the best supplier based on total landed costs and lead time.
            Show exact Calculations to get the correct landed cost, this will help you in evaluating the best suppliers.

            Calculate the final landed cost for each supplier based on import duty/tariffs shared to you by **tariff correction agent**.

            Remember:
            - Perform this calculation for every single supplier including supplier even if in the same country.
            - only after this select the best supplier basis total landed cost.
            """,
        )

        tariff_correction_agent = ConversableAgent(
            "tariff_correction_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **tariff_correction_agent**.
            # Role:
            You are provided with a user query, your job is to study the tariff changes from and to countries and prepare a dictionary as explained below.

            Think Step by Step:
            - Study the user query very carefully.
            - What is the country from and what is the country to ?
            - What is the new tariff ?
            - now read the table given to you by **logistics_tracker_agent** and update values and return the table.

            Remember: Just change the values for which the tariffs have been updated, otherwise keep the same import duty as before,
            ensure that you share all rows [whether tariffs have been increased or not].
            """,
        )

        logistics_tracker_agent = ConversableAgent(
            "logistics_tracker_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **logistics_tracker_agent**.
            # Role:
            Your task is to initiate the **update_import_duties** tool that is alloted to you when a user says about change in tariffs or import duty. 
            

            Think Step by Step:

            - What is the country from and what is the country to ?
            - What is the new tariff ?
            - now prepare  update variable: {('country_from','country_to'): 'tariff_percentage'}


            While using **update_import_duties** tool, params have to be sent in following format:
            
            updates (dict): A dictionary where each key is a tuple (supplier, delivery)
            and the value is the new import duty (as a string, e.g., '35%').

            Example:

                ```

                    updates = {
                        ('China', 'USA'): '35%',
                        ('India', 'USA'): '30%'
                    }

                ```
            """,
        )

        supplier_analysis_agent = ConversableAgent(
            "supplier_analysis_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message=f"""
            # Basic Information:
            You are **supplier_analysis_agent**.
            # Role:
            Identify the Item numbers, use the **get_best_suppliers** tool to find best supplier for that specific item numbers.

            Always make use of the **get_best_suppliers** tool to get the most accurate results.

            These are the delivery locations:
            
            {pd.read_csv('./updated_docs/Supplier_data.csv')["Delivery location"].unique()}"
            """,
        )

        register_function(
            get_best_suppliers,
            caller=supplier_analysis_agent,
            executor=supplier_analysis_agent,
            name="get_best_suppliers",
            description=f"""Use this tool to get top suppliers for a specific item to a delivery location for all supplying countries.\nWrite Item number in this format: ITM-001 or ITM-002. \nThese are the delivery locations: {pd.read_csv('./updated_docs/Supplier_data.csv')["Delivery location"].unique()}""",
        )

        register_function(
            update_import_duties,
            caller=logistics_tracker_agent,
            executor=logistics_tracker_agent,
            name="update_import_duties",
            description="""Use this tool to get import duties. While this tool, params have to be sent in following format:
            
            updates (dict): A dictionary where each key is a tuple (supplier, delivery)
            and the value is the new import duty (as a string, e.g., '35%').

            Example:

                ```

                    updates (dict): {('China', 'USA'): '35%', ('India', 'USA'): '30%'}

                ```
            """,
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Step-by-Step Reasoning

            1. **Interpret** the user's question in full.  
            2. **Decompose** it into atomic sub-questions or metrics to compute (e.g., "What's the average lead time?" , "How did expedited shipping affect costs?").  
            3. **Examine** every table provided—consider relationships, joins, and cross-table comparisons.  
            4. **Perform calculations** (differences, ratios, averages, growth rates, correlations, etc.) to surface insights that aren't immediately visible.  
            5. **Validate** that every conclusion is directly supported by the data; do not introduce unsupported assumptions.

            ---

            ## Some Examples of Thinking:

            Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

            Thought process: Here, user is seeking an alternate supplier for specified Items, they are asking to consider tariffs on China and India, but that doesn't mean that they want suppliers only from China or India, infact they want you to look at all possible suppliers check the overall impact on all suppliers for tariffs and then calculate cost after impact. So a supplier from USA might be best or based on tariff change if the cost comes down then that particular country's supplier might be the best.



            **Q: Suggest options to expedite existing open purchase order (PO-103916) with cost/lead time impact:**

            **Thought Process: Maybe you can look to expedite by switching from sea to air transportation, and hence make joins accordingly for that specific supplier.**
            
            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. **User Requirements** [Never Skip]
            - Enlist the exact user requirements here, these are important details
            - This helps user to track how you came up with the answer (increases accountability)


            2. **Markdown Table** [Never Skip] 
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Only select useful columns that are contributing to final answer or ones that satisfy the main user query.
            - Only select unique and useful rows after careful consideration, this is essential to reduce user frustration.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (≥ 100 words)**  
            - Place **immediately after** its corresponding table.  
            - Grounded entirely in the supplied data and your calculations.  
            - Highlight patterns, anomalies, comparisons, and their business or operational implications.  
            - Reference specific table rows or calculated values to justify each point.
            - These insights should be in bulleted format ONLY.

            Repeat the "table → insight" sequence until **every** sub-query has been answered.


            Finally:
            Segue smoothly into Asking if the user has any other questions, maybe you can give some possible follow-up questions like drafting a PO, sending out an email regarding a drafted po.
            Think intelligently and map follow-up questions according to your answer and situation.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > "A meaningful report cannot be generated due to lack of complete data."  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your "table → insight" series in one concise, data-grounded response.

            **IMPORTANT: End your response with "TERMINATE" to properly conclude the analysis workflow.**

            """
        )

        agent_list = [
            you,
            tariff_correction_agent,
            logistics_tracker_agent,
            supplier_analysis_agent,
            supplier_evaluation_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [supplier_analysis_agent],
            supplier_analysis_agent: [logistics_tracker_agent],
            logistics_tracker_agent: [logistics_tracker_agent, tariff_correction_agent],
            tariff_correction_agent: [supplier_evaluation_agent],
            supplier_evaluation_agent: [optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=25,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def expedite_supply_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
                You are **p2p_compliance_agent**.
            # Role:
                "Your task is to initiate the **get_open_po_data** tool that is allotted to you.\n"
                "Extract PO number from user query and pass it to the tool."
                "If PO number is not explicitly mentioned in new query, take PO from Chat Summary "
                "in the format: 'PO-XXXXXX'."
            """,
        )

        logistics_tracker_agent = ConversableAgent(
            "logistics_tracker_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Role: logistics_tracker_agent
                
                You are the **logistics_tracker_agent**.  
                Your primary responsibility is to initiate the **get_avg_lead_time** tool whenever the user asks about delivery times, shipment planning, or transportation modes.  

            # Rules for Mode of Transport:
                - If the user asks for **fastest delivery**, **expedited shipping**, or if the query is based on **impact of lead time** → use **Air** as the mode of transport.  
                - For all other cases → use **Sea** as the mode of transport.  

            # Expected Behavior:
                1. Understand the user's query regarding shipment lead times.  
                2. Decide the transport mode (Air or Sea) based on the above rules.  
                3. Call the `get_avg_lead_time` tool with the selected mode of transport.  
                4. Provide a clear, concise response to the user with the retrieved lead time.  

            # Example Guidance:
                - **User:** "What's the average lead time for urgent shipments from China to Germany?"  
                **Agent:** Choose **Air** → call `get_avg_lead_time(mode="Air")`.  

                - **User:** "Tell me the lead time for bulk shipments from India to USA."  
                **Agent:** Choose **Sea** → call `get_avg_lead_time(mode="Sea")`.
            """,
        )

        supplier_analysis_agent = ConversableAgent(
            "supplier_analysis_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **supplier_analysis_agent**.
            # Role:
            Your task is to initiate the **expedite_po_tool** tool that is alloted to you. Extract PO number from user query and pass it to the tool.
            in the format: 'PO-XXXXXX'
            """,
        )

        register_function(
            get_avg_lead_time,
            caller=logistics_tracker_agent,
            executor=logistics_tracker_agent,
            name="get_avg_lead_time",
            description="Use this tool to get average lead times for open purchase orders",
        )

        register_function(
            get_open_po_data,
            caller=p2p_compliance_agent,
            executor=p2p_compliance_agent,
            name="get_open_po_data",
            description="Use this tool to get Data regarding Open Purchase order based on PO Number",
        )

        register_function(
            expedite_po_by_lead,
            caller=supplier_analysis_agent,
            executor=supplier_analysis_agent,
            name="expedite_po_by_lead",
            description="Helps in calculating expedite options on the basis of, fastest shipping possible (always go for this in case they just mention expedite a purchase order)",
        )

        register_function(
            expedite_po_by_cost,
            caller=supplier_analysis_agent,
            executor=supplier_analysis_agent,
            name="expedite_po_by_cost",
            description="Helps in calculating expedite options on the basis of low impact on cost, (go for this tool only if users asks for partial expediting or alternate expediting suggestion.)",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Step-by-Step Reasoning

            1. **Interpret** the user's question in full.  
            2. **Decompose** it into atomic sub-questions or metrics to compute (e.g., "What's the average lead time?" , "How did expedited shipping affect costs?").  
            3. **Examine** every table provided—consider relationships, joins, and cross-table comparisons.  
            4. **Perform calculations** (differences, ratios, averages, growth rates, correlations, etc.) to surface insights that aren't immediately visible.  
            5. **Validate** that every conclusion is directly supported by the data; do not introduce unsupported assumptions.

            ---

            ## Some Examples of Thinking:

            Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

            Thought process: Here, user is seeking an alternate supplier for specified Items, they are asking to consider tariffs on China and India, but that doesn't mean that they want suppliers only from China or India, infact they want you to look at all possible suppliers check the overall impact on all suppliers for tariffs and then calculate cost after impact. So a supplier from USA might be best or based on tariff change if the cost comes down then that particular country's supplier might be the best.



            **Q: Suggest options to expedite existing open purchase order (PO-103916) with cost/lead time impact:**

            **Thought Process: Maybe you can look to expedite by switching from sea to air transportation, and hence make joins accordingly for that specific supplier.**
            
            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. **User Requirements** [Never Skip]
            - Enlist the exact user requirements here, these are important details
            - This helps user to track how you came up with the answer (increases accountability)


            2. **Markdown Table** [Never Skip] 
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Only select useful columns that are contributing to final answer or ones that satisfy the main user query.
            - Only select unique and useful rows after careful consideration, this is essential to reduce user frustration.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (≥ 100 words)**  
            - Place **immediately after** its corresponding table.  
            - Grounded entirely in the supplied data and your calculations.  
            - Highlight patterns, anomalies, comparisons, and their business or operational implications.  
            - Reference specific table rows or calculated values to justify each point.
            - These insights should be in bulleted format ONLY.

            Repeat the "table → insight" sequence until **every** sub-query has been answered.


            Finally:
            Segue smoothly into Asking if the user has any other questions, maybe you can give some possible follow-up questions like drafting a PO, sending out an email regarding a drafted po.
            Think intelligently and map follow-up questions according to your answer and situation.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > "A meaningful report cannot be generated due to lack of complete data."  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your "table → insight" series in one concise, data-grounded response.

            **IMPORTANT: End your response with "TERMINATE" to properly conclude the analysis workflow.**

            """
        )

        agent_list = [
            you,
            p2p_compliance_agent,
            logistics_tracker_agent,
            supplier_analysis_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [
                p2p_compliance_agent
            ],
            p2p_compliance_agent: [p2p_compliance_agent, logistics_tracker_agent],
            logistics_tracker_agent: [logistics_tracker_agent, supplier_analysis_agent],
            supplier_analysis_agent: [supplier_analysis_agent, optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini}
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def extract_invoice_details_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **p2p_compliance_agent**.
            # Role:
            Your task is to initiate the **get_po_grn_details** tool that is alloted to you **for each Invoice that has been attached**. 
            Extract PO number and GRN from user query and pass it to the tool. If PO number or GRN is not explicitly mentioned in new query, take PO and GRN from  **Chat Summary of Previous Conversation:**
            
            PO in the format: 'PO-XXXXXX'
            """,
        )

        documentation_agent = ConversableAgent(
            "documentation_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:

            You are **documentation_agent**.
           
            # Role:
            
            Your job is to run the **extract_invoice_details** tool to extract details present in invoice.
            """,
        )

        logistics_tracker_agent = ConversableAgent(
            "logistics_tracker_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=10,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:

            You are **logistics_tracker_agent**.
           
            # Role:
            
            Your job is to calculate the total landed cost, after import duty is applied. So, take the PO data and details extracted from Invoice and check if total import value and total landing cost match the invoice details.

            Perform proper calculations and then provide result in table + your insight.

            For your convenience, I have provided the import duties:


            | Supplier Location | Delivery Location | Import Duty |
            |------------------|-------------------|-------------|
            | China            | Philippines        | 6%          |
            | China            | USA                | 12%         |
            | China            | Taiwan             | 8%          |
            | Japan            | Philippines        | 9%          |
            | Japan            | USA                | 12%         |
            | Japan            | Taiwan             | 7%          |
            | USA              | Philippines        | 14%         |
            | USA              | USA                | 0%          |
            | USA              | Taiwan             | 10%         |
            | India            | Philippines        | 10%         |
            | India            | USA                | 10%         |
            | India            | Taiwan             | 9%          |
            | Germany          | Philippines        | 12%         |
            | Germany          | USA                | 12%         |
            | Germany          | Taiwan             | 10%         |
            | Taiwan           | Philippines        | 8%          |
            | Taiwan           | USA                | 15%         |
            | Taiwan           | Taiwan             | 0%          |
            """,
        )

        register_function(
            get_po_grn_details,
            caller=p2p_compliance_agent,
            executor=p2p_compliance_agent,
            name="get_po_grn_details",
            description="Use this tool to get Data regarding Purchase order based on PO Number and Goods Recieved Note based on GRN.",
        )

        register_function(
            extract_invoice_details,
            caller=documentation_agent,
            executor=documentation_agent,
            name="extract_invoice_details",
            description="""Use this tool to extract all details from the Invoice PDF.""",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Step-by-Step Reasoning

            1. **Interpret** the user's question in full.  
            2. **Decompose** it into atomic sub-questions or metrics to compute (e.g., “What's the average lead time?”, “How did expedited shipping affect costs?”).  
            3. **Examine** every table provided—consider relationships, joins, and cross-table comparisons.  
            4. **Perform calculations** (differences, ratios, averages, growth rates, correlations, etc.) to surface insights that aren't immediately visible.  
            5. **Validate** that every conclusion is directly supported by the data; do not introduce unsupported assumptions.

            ---

            ## Some Examples of Thinking:

            Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

            Thought process: Here, user is seeking an alternate supplier for specified Items, they are asking to consider tariffs on China and India, but that doesn't mean that they want suppliers only from China or India, infact they want you to look at all possible suppliers check the overall impact on all suppliers for tariffs and then calculate cost after impact. So a supplier from USA might be best or based on tariff change if the cost comes down then that particular country's supplier might be the best.



            **Q: Suggest options to expedite existing open purchase order (PO-103916) with cost/lead time impact:**

            **Thought Process: Maybe you can look to expedite by switching from sea to air transportation, and hence make joins accordingly for that specific supplier.**
            
            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. Only Study the data provided by User, **documentation_agent** and **p2p_compliance_agent**. Then check if they match.
               In case  **documentation_agent** doesn't provide any valid details at all to compare, mention that and mention the fact that they user hasn't uploaded a valid invoice.
               Provide exact shipping modality, provide exact supplier code in the table, provide per unit costs and then total cost.


            2. **Markdown Table** [Never Skip: prepare table by combining ALL details provided by **documentation_agent** and **p2p_compliance_agent** agents. Also include exact GRN Number in the table along with other details]
            - Compare PO, Invoice and GRN in separate rows of the same table.
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (≥ 100 words)**  
            - Mention whether the attached Invoice and GRN are matching in terms of Quantity, Unit Costs etc.
            - Also Check for other details from PO, it is possible that total ordered quantity wasn't received but it is okay as long as Invoice and GRN details regarding recieved quantity are matching.
            - Give basic explanation

            - Now add title called "Action Item": Finally Give Action Item based on if it matches mention that PO, Invoice and GRN is matched and confirmed values are correct and ready to release for payment. Mention Receiving location and Shipping location. Use ✅ or ❌ to indicate valid or invalid matching.
           
            Repeat the “table → insight” sequence until **every** sub-query has been answered.


            ### Finally:
            
                Segue smoothly into Asking if the user has any other questions, like:
                
                - If the PO, Invoice and GRN matches then ask whether the user [Procument Manager: Priya Sharma] wants to send a mail notifying release of payment to the financial team.
                - If the PO, Invoice and GRN does not match, then ask whether the user [Procument Manager: Priya Sharma] wants to send a mail to the supplier seeking clarification for the error in invoice and/or rectified invoice.


            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > “A meaningful report cannot be generated due to lack of complete data.”  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your “table → insight” series in one concise, data-grounded response.

            """,
        )

        agent_list = [
            you,
            documentation_agent,
            p2p_compliance_agent,
            logistics_tracker_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [documentation_agent, logistics_tracker_agent],
            documentation_agent: [documentation_agent, p2p_compliance_agent],
            p2p_compliance_agent: [p2p_compliance_agent, optibuy_agent],
            logistics_tracker_agent: [logistics_tracker_agent, optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
            system_message=f"""
            Choose p2p_compliance agent if user asks for Three way PO matching with Invoice and GRN Note. Choose logistics tracker agent only if user asks to check tax value and total landing cost.
            """
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def seek_supplier_correction_email_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        email_sending_agent = ConversableAgent(
            "email_sending_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message=f"""
            You are **email\_sending\_agent**.

            Your Task is to seek clarification from the supplier on incorrect values present in their Invoice when compared with the GRN
            and PO Data.

            Extract all details from Invoice and specifically mention the errors.

            Write Email in a calm and calculated manner as to inform of the errors. Do not accuse the supplier. Just mention the Inaccuracies and seek clarification and/or corrected Invoice.

            This is the format [focus only on the styling, Extract relevant issues only] in which the mail has to be sent:


            You are supposed to use the **email_sending_tool_generic** tool to send the email to seek clarification from supplier.
            
----



                    <!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    /* Reset and base */
    body {{
      margin: 0;
      padding: 0;
      background-color: #F9FAFB;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #1F2937;
      line-height: 1.5;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    /* Container to center content */
    .container {{
      max-width: 600px;
      margin: 0 auto;
      padding: 24px;
    }}

    /* Card with subtle shadow and rounded corners */
    .card {{
      background-color: #FFFFFF;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(31, 41, 55, 0.1);
      overflow: hidden;
    }}

    /* Accent bar at top of card */
    .accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, #2563EB, #8B5CF6);
    }}

    /* Header inside card */
    .card-header {{
      padding: 24px;
    }}

    .card-header h2 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: #4F46E5;
      /* Purple */
    }}

    .card-header p.date {{
      margin-top: 4px;
      font-size: 0.875rem;
      color: #6B7280;
    }}

    /* Body content */
    .card-body {{
      padding: 0 24px 24px;
    }}

    .card-body p {{
      margin: 16px 0;
      font-size: 1rem;
      color: #374151;
    }}

    /* Table styling */
    .details-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
    }}

    .details-table th,
    .details-table td {{
      padding: 12px 16px;
      text-align: left;
    }}

    .details-table thead th {{
      background-color: #E0E7FF;
      /* Light indigo */
      color: #4F46E5;
      /* Purple */
      font-weight: 600;
    }}

    .details-table tbody tr {{
      border-bottom: 1px solid #E5E7EB;
    }}

    .details-table tbody tr:nth-child(even) {{
      background-color: #F3F4F6;
    }}

    .details-table td {{
      color: #374151;
      font-weight: 500;
    }}

    /* Footer */
    .footer {{
      font-size: 0.75rem;
      color: #9CA3AF;
      text-align: center;
      margin: 16px 0;
    }}

    /* Responsive adjustments */
    @media (max-width: 600px) {{
      .container {{
        padding: 16px;
      }}

      .card-header h2 {{
        font-size: 1.25rem;
      }}

      .details-table th,
      .details-table td {{
        padding: 8px 12px;
      }}
    }}
  </style>
</head>

<body>
  <div class="container">
    <div class="card">
      <div class="accent-bar"></div>
      <div class="card-header">
        <h2>Inaccuracies in Invoice: [Invoice Number]</h2>
        <p class="date"><strong>Date:</strong> {datetime.now().strftime('%d-%m-%Y ( at %H:%M )')}</p>
        <p>Authorized by Procurement Mananger: <b>Priya Sharma</b></p>
      </div>
      <div class="card-body">
        <p>Dear Supplier Team,</p>
        <p>OptiBuy has found some inaccuracies in your Invoice: [Invoice Number]. Below are the details:</p>
        <p>[MENTION THE INACCURACIES, DO NOT MENTION THE EXACT GRN NUMBER, JUST MENTION THE PO NUMBER]</p>
        <p>[SEEK CLARIFICATION]</p>
        <table class="details-table">
          
        </table>
        <p style="color:#4F46E5;">For further assistance, please reference this PO number in any correspondence with the procurement manager:
          Priya Sharma.</p>
        <p class="footer">This is an automated email sent by ProcureWise AI. Do not reply directly to this email.</p>
      </div>
    </div>
  </div>
</body>

</html>


---

Also Provide a Subject Line for the same.

---

Also Provide a post sending message for the same
            """,
        )

        register_function(
            email_sending_tool_generic,
            caller=email_sending_agent,
            executor=email_sending_agent,
            name="email_sending_tool_generic",
            description="Send an email using this tool only if user confirms/authorises you to send the email. Pass the Subject First and then the HTML_BODY",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            email_sending_agent
        ]

        transitions_list = {
            you: [email_sending_agent],
            email_sending_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def read_pr_emails_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        email_agent = ConversableAgent(
            "email_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            
Read PR Request emails and send them to **p2p_compliance_agent** to extract so that it can be prepared for PR release.


            """,
        )

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message=f"""
            
            You are an information extraction assistant. When given a request message related to procurement or purchase requisition, extract and return the following details in a clean, structured format. Ensure all field names and their corresponding values are displayed exactly as specified below:

            # Extract the following fields:

            - Assigned PR Number: [Take 'PR-103201' by default]

            - Requester

            - Designation

            - Location

            - Mode of Delivery: [Sea (by default)]

            - Item Number

            - Item Name

            - Quantity

            - Need By Date

            - Preferred Supplier

            - Cost Center

            - Storage Location (Sloc)

            - Related Production Order

            - Priority: [Guess based on current date: {datetime.now().strftime('%d-%m-%Y ( at %H:%M )')} and Need by Date. By Default: High]

            ## Formatting Instructions:

            - Display the extracted fields in the exact order shown above.

            - Use bold labels followed by a colon and a space (e.g., Item Name: Logic Chip).

            - Use line breaks to separate each field.

            - Do not include any additional commentary or text outside of the extracted fields.

            - If a field is not explicitly mentioned in the input, do not mention it in your response.


            You are talking to Procurement Manager: Priya Sharma. Finally in a professional manner ask if the user wants to release the PR with above details.

            """,
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. Only Study the data provided by **email_agent** and **p2p_compliance_agent**. 


            2. **Markdown Table** [Never Skip]
            - Prepare table about the PR details provided by **p2p_compliance_agent**.
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (< 30 words)**  
            - Give basic explanation
           
            Repeat the “table → insight” sequence until **every** sub-query has been answered.


            ### Finally:
            
                Segue smoothly into Asking if the user has any other questions, like:
                
                - If the user [Procument Manager: Priya Sharma] wants to confirm PR and send an email to the 1st stage approver. Also add the details from the PR extraction into ERP System.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > “A meaningful report cannot be generated due to lack of complete data.”  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your “table → insight” series in one concise, data-grounded response.

            """
        )

        register_function(
            fetch_pr_emails,
            caller=email_agent,
            executor=email_agent,
            name="fetch_pr_emails",
            description="Use this tool to read unread Purchase Requistion request emails.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            email_agent,
            p2p_compliance_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [email_agent],
            email_agent: [p2p_compliance_agent],
            p2p_compliance_agent: [optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def send_pr_to_approver_email_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        email_sending_agent = ConversableAgent(
            "email_sending_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message=f"""
            You are **email\_sending\_agent**.

            Your Task is to send a mail to the First Approver regarding a PR request.

            Extract all details from PR request and .

            Write Email in a calm and calculated manner as to inform of the errors. Do not accuse the supplier. Just mention the Inaccuracies and seek clarification and/or corrected Invoice.

            This is the format [focus only on the styling, Extract relevant issues only] in which the mail has to be sent:

            You are supposed to use the **email_sending_tool_generic** tool to send the email to seek clarification from supplier.
            
----



                    <!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    /* Reset and base */
    body {{
      margin: 0;
      padding: 0;
      background-color: #F9FAFB;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #1F2937;
      line-height: 1.5;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    /* Container to center content */
    .container {{
      max-width: 600px;
      margin: 0 auto;
      padding: 24px;
    }}

    /* Card with subtle shadow and rounded corners */
    .card {{
      background-color: #FFFFFF;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(31, 41, 55, 0.1);
      overflow: hidden;
    }}

    /* Accent bar at top of card */
    .accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, #2563EB, #8B5CF6);
    }}

    /* Header inside card */
    .card-header {{
      padding: 24px;
    }}

    .card-header h2 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: #4F46E5;
      /* Purple */
    }}

    .card-header p.date {{
      margin-top: 4px;
      font-size: 0.875rem;
      color: #6B7280;
    }}

    /* Body content */
    .card-body {{
      padding: 0 24px 24px;
    }}

    .card-body p {{
      margin: 16px 0;
      font-size: 1rem;
      color: #374151;
    }}

    /* Table styling */
    .details-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0;
    }}

    .details-table th,
    .details-table td {{
      padding: 12px 16px;
      text-align: left;
    }}

    .details-table thead th {{
      background-color: #E0E7FF;
      /* Light indigo */
      color: #4F46E5;
      /* Purple */
      font-weight: 600;
    }}

    .details-table tbody tr {{
      border-bottom: 1px solid #E5E7EB;
    }}

    .details-table tbody tr:nth-child(even) {{
      background-color: #F3F4F6;
    }}

    .details-table td {{
      color: #374151;
      font-weight: 500;
    }}

    /* Footer */
    .footer {{
      font-size: 0.75rem;
      color: #9CA3AF;
      text-align: center;
      margin: 16px 0;
    }}

    /* Responsive adjustments */
    @media (max-width: 600px) {{
      .container {{
        padding: 16px;
      }}

      .card-header h2 {{
        font-size: 1.25rem;
      }}

      .details-table th,
      .details-table td {{
        padding: 8px 12px;
      }}
    }}
  </style>
</head>

<body>
  <div class="container">
    <div class="card">
      <div class="accent-bar"></div>
      <div class="card-header">
        <h2>New PR Request: [PR Request Number]</h2>
        <p class="date"><strong>Date:</strong> {datetime.now().strftime('%d-%m-%Y ( at %H:%M )')}</p>
        <p>Authorized by Procurement Mananger: <b>Priya Sharma</b></p>
      </div>
      <div class="card-body">
        <p>Dear Supplier Team,</p>
        <p>OptiBuy has received a new PR request: [PR Request Number]. Below are the details:</p>

        <table class="details-table">
          [mention the details in proper HTML table format, please adhere to styling | Extract Key details from previous message]
        </table>
        <p style="color:#4F46E5;">For further assistance, please reference this PR number in any correspondence with the procurement manager:
          Priya Sharma.</p>
        <p class="footer">This is an automated email sent by ProcureWise AI. Do not reply directly to this email.</p>
      </div>
    </div>
  </div>
</body>

</html>


---

Also Provide a Subject Line for the same. [Approval Request]

---

Also Provide a Post sending message for the same.
            """,
        )

        register_function(
            email_sending_tool_generic,
            caller=email_sending_agent,
            executor=email_sending_agent,
            name="email_sending_tool_generic",
            description="Send an email using this tool only if user confirms/authorises you to send the email. Pass the Subject First and then the HTML_BODY",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            email_sending_agent
        ]

        transitions_list = {
            you: [email_sending_agent],
            email_sending_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def pr_pending_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        p2p_compliance_agent = ConversableAgent(
            "p2p_compliance_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            
            # Role:

            You are p2p_compliance_agent.

            # Task:

            Your task is to look up pending approval stage details for any PR numbers the user provides.
            When the user names one or more PR numbers, call the **analysed_pr_details** tool and pass it the list of PR numbers exactly as given.
            If the tool returns a markdown table of results, send that table back to the user.
            """,
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. Only Study the data provided by **email_agent** and **p2p_compliance_agent**. 


            2. **Markdown Table** [Never Skip]
            - Prepare tables about the details provided by **p2p_compliance_agent**. EVERY SINGLE TABLE THAT **p2p_compliance_agent** has prepared.
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (< 30 words)**  
            - Give very basic explanation in less than 30 words.
           
            Repeat the “table → insight” sequence until **every** sub-query has been answered.


            ### Finally:
            
                Segue smoothly into Asking if the user has any other questions, like:
                
                - If the user [Procument Manager: Priya Sharma] wants you to send a reminder email to the approver with whom the PR stages are pending, you can optionally mention the mail id of the approver as well.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > “A meaningful report cannot be generated due to lack of complete data.”  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your “table → insight” series in one concise, data-grounded response.

            """
        )

        register_function(
            analysed_pr_details,
            caller=p2p_compliance_agent,
            executor=p2p_compliance_agent,
            name="analysed_pr_details",
            description="Use this tool to read unread Purchase Requistion request emails.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            p2p_compliance_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [p2p_compliance_agent],
            p2p_compliance_agent: [optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def send_pr_reminder_email_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        email_sending_agent = ConversableAgent(
            "email_sending_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            You are **email\_sending\_agent**.

            Your Task is to send a reminder mail to the Current Approver regarding a PR request.

            Extract all details from PR request

            Extract PR that is pending for approval only.

            Format of PR: "PR-XXXXXX"

            Format should be matched exactly.

            **CRITICAL**: Make use of Tool: **send_reminder_email_to_approver** to send reminder. 
            DO NOT use email_sending_tool - that is for PO (Purchase Order) emails only. 
            You MUST use send_reminder_email_to_approver for PR (Purchase Requisition) reminders.
            """,
        )

        register_function(
            send_reminder_email_to_approver,
            caller=email_sending_agent,
            executor=email_sending_agent,
            name="send_reminder_email_to_approver",
            description="Send a reminder email to current approver, reminding them to approve a pending PR using this tool only if user confirms/authorises you to send the email.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            email_sending_agent
        ]

        transitions_list = {
            you: [email_sending_agent],
            email_sending_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def calculate_pr_schedule_changes_workflow(orchestration_mssg: list, query: str, chat_summary: str):

    print("Chat Summary:\n\n"+chat_summary)
    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")

        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New  Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:

        supplier_analysis_agent = ConversableAgent(
            "supplier_analysis_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message="""
            You are **email\_sending\_agent**.

            Your Task is to calculate scheduled changes for a PR request.

            Extract all details from PR request.

            Format of PR: "PR-XXXXXX" 

            Format should be matched exactly.

            Make use of Tool: **calculate_eta_from_files** to send reminder.
            """,
        )

        register_function(
            calculate_eta_from_files,
            caller=supplier_analysis_agent,
            executor=supplier_analysis_agent,
            name="calculate_eta_from_files",
            description="Calculate scheduled changes for a specific PR using this tool.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=1,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. Only Study the data provided by **supplier_analysis_agent**. 


            2. **Markdown Table** [Never Skip]
            - Prepare table about the PR details provided by **supplier_analysis_agent**.
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (< 200 words)**  
            - Give explanation of the table.
           
            Repeat the “table → insight” sequence until **every** sub-query has been answered.


            ### Finally:
            
                Segue smoothly into Asking if the user has any other questions, like:
                
                - If the user [Procument Manager: Priya Sharma] wants to confirm PR and send an email to the 1st stage approver. Also add the details from the PR extraction into ERP System.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > “A meaningful report cannot be generated due to lack of complete data.”  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your “table → insight” series in one concise, data-grounded response.

            """
        )

        agent_list = [
            you,
            supplier_analysis_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [supplier_analysis_agent],
            supplier_analysis_agent: [optibuy_agent],
            optibuy_agent: [you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Preparing plan for execution. Selecting relevant agents",
            "role": "assistant",
            "name": "optibuy_agent"
        }
        ]

        orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:

        print(err)
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the agentic workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


def clean_agent_messages(chat_history):
    """
    Process chat history to remove raw function outputs and keep only markdown content.
    Handles dict, stringified dict (including np.int64/np.float64), and string content.
    """
    cleaned_history = []
    for message in chat_history:
        content = message.get('content')
        # If content is a dict with 'markdown_output', extract it
        if isinstance(content, dict) and 'markdown_output' in content:
            message['content'] = content['markdown_output']
            cleaned_history.append(message)
            continue
        # If content is a string that looks like a dict, try to parse it
        if isinstance(content, str) and content.strip().startswith('{') and 'markdown_output' in content:
            # Preprocess: Replace np.int64(...) and np.float64(...) with int(...) and float(...)
            content_clean = re.sub(r'np\.int64\((\d+)\)', r'int(\1)', content)
            content_clean = re.sub(r'np.int64\((\d+)\)',
                                   r'int(\1)', content_clean)
            content_clean = re.sub(
                r'np.float64\(([\d\.]+)\)', r'float(\1)', content_clean)
            try:
                parsed = ast.literal_eval(content_clean)
                if isinstance(parsed, dict) and 'markdown_output' in parsed:
                    message['content'] = parsed['markdown_output']
                    cleaned_history.append(message)
                    continue
            except Exception as e:
                print("Failed to parse string as dict:", e)
        # If content is a string, keep the existing logic for panama_analysis_agent
        if message.get('name') == 'panama_analysis_agent' and content:
            if "{'markdown_output':" in content or '"markdown_output":' in content:
                try:
                    if '**PANAMA CANAL' in content:
                        start = content.find('**PANAMA CANAL')
                        end = content.find("'}", start)
                        if end == -1:
                            end = content.find('"}', start)
                        if start != -1 and end != -1:
                            markdown_only = content[start:end]
                            message['content'] = markdown_only
                except Exception as e:
                    print("Error extracting markdown from string:", e)
            if isinstance(message['content'], str) and message['content'].strip().startswith('{') and 'markdown_output' in message['content']:
                continue
        cleaned_history.append(message)
    return cleaned_history


def panama_canal_workflow(orchestration_mssg: list, query: str, chat_summary: str):
    """Dedicated workflow for Panama Canal delay analysis"""
    print("Panama Canal Analysis Workflow Started")
    print("Chat Summary:\n\n"+chat_summary)

    if chat_summary.strip() != "":
        print("CHAT SUMMARY:\n`"+chat_summary+"`")
        final_query = f"""
        **Chat Summary of Previous Conversation:** {chat_summary}
        \n
        **New Query:** {query}
        """
    else:
        final_query = query

    start_time = time.time()
    try:
        # Panama Canal Analysis Agent - handles initial delay analysis
        panama_analysis_agent = ConversableAgent(
            "panama_analysis_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=5,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **panama_analysis_agent**.
            
            # Role:
            You handle Panama Canal delay analysis and provide structured data for financial analysis.
            
            # Key Tasks:
            1. Extract delay days (default: 15 days if not specified)
            2. ALWAYS start with get_delayed_shipments_to_east_coast to identify ALL delayed shipments
            3. Analyze which DCs have the highest-value delayed shipments and focus on the most critical ones first
            4. ALWAYS use recommend_container_rerouting for the most critical affected DC
            
            # REQUIRED Function Call Sequence:
            You MUST call these functions in order:
            1. get_delayed_shipments_to_east_coast(affected_dc='DC3', delay_days=15)
            2. recommend_container_rerouting(delayed_shipments_data=<result_from_step_1>)
            
            # Output Instructions:
            When you receive function results:
            1. If the result contains a 'markdown_output' field, display that content
            2. Do not display raw Python dictionaries or JSON structures
            3. Keep the full result data to pass to the next function
            4. Focus on presenting clean, formatted tables and analysis
            
            # Function Data Passing:
            - When calling recommend_container_rerouting, pass the COMPLETE dict from get_delayed_shipments_to_east_coast
            - This ensures proper data flow between functions
            
            # After Analysis:
            Once both functions have been called, provide a summary:
            - Analysis complete for [DC name]
            - Number of delayed shipments identified
            - Total value at risk
            - Rerouting options found (if any)
            - Ready for financial impact analysis
            """,
        )
        # Supply Chain Risk Agent - handles stockout and cost-benefit analysis
        supply_risk_agent = ConversableAgent(
            "supply_risk_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=5,
            human_input_mode='NEVER',
            system_message="""
            # Basic Information:
            You are **supply_risk_agent**.
            
            # Role:
            You perform financial analysis using data from panama_analysis_agent.
            
            # CRITICAL DATA EXTRACTION:
            1. Look for "Response from calling tool" messages in the conversation
            2. Extract the delayed_shipments_data from get_delayed_shipments_to_east_coast
            3. Look for rerouting summary that contains:
            - "Total Rerouting Cost: $1,650.00" (or similar)
            - "Recommendation: PROCEED with rerouting"
            
            # Function Call Instructions:
            When you see rerouting recommendations like:
            - "Total Rerouting Cost: $1,650.00"
            - "1 viable rerouting options"
            
            Create a rerouting_data dict:
            {
                'markdown_output': '[the rerouting text]',
                'total_rerouting_cost': 1650.0,
                'container_information': [{'po_number': 'PO-103984', ...}]
            }
            
            Then call:
            calculate_financial_impact_and_recommendation(
                delayed_shipments_data=[from first function],
                rerouting_data=[constructed dict with cost info]
            )
            
            # Expected Behavior:
            If rerouting options exist with costs, they should appear in the financial analysis.
            The output should show cost-benefit comparison, not "NO REROUTING OPTIONS".
            """,
        )

        # Final Report Agent - synthesizes all analysis into actionable insights
        optibuy_agent = ConversableAgent(
            "optibuy_agent",
            llm_config={"config_list": config_list_gpt_4o_mini},
            max_consecutive_auto_reply=3,
            human_input_mode='NEVER',
            system_message=f"""
            # Role Definition

            You are **optibuy_agent**, an analytical reasoning agent specialized in generating structured reports and data-driven insights from tabular data.
            You are talking to Priya Sharma [a procurement manager], while answering make sure to address the user with their name (act as their copilot).

            Always add extra spacing/new-lines so that the output response looks uncluttered.

            ---

            ## Special Handling for Rerouting Approvals

            **IMPORTANT**: If the user's message contains any of these approval keywords/phrases:
            - "update the PO"
            - "please update PO"
            - "kindly update the PO"
            - "proceed with rerouting"
            - "go ahead with the rerouting"
            - "approve the rerouting"
            - "inform the travel planners"
            - "inform transport planners"
            - "notify the logistics team"

            **RESPOND IMMEDIATELY with this exact format:**

            ---

            **✅ REROUTING APPROVAL CONFIRMED**

            Hi Priya,

            I've successfully processed your rerouting approval:

            **Actions Completed:**
            • ✅ **Purchase Order Updated** - PO destinations have been modified to reflect the new routing plan
            • ✅ **Travel Planners Notified** - Email sent to transport logistics team with updated routing instructions
            • ✅ **Cost Adjustments Applied** - Rerouting costs have been factored into the PO totals

            **Next Steps:**
            - Transport team will coordinate the container rerouting within 24 hours
            - You'll receive email confirmation once shipments are redirected
            - Tracking updates will be provided as containers reach new destinations

            The rerouting is now in motion to minimize the Panama Canal delay impact!

            ---

            **Do NOT generate any tables or analysis when handling approval requests - just provide the confirmation above.**

            ---


            I will supply you with:  
            1. A **natural-language query** (via the `you` agent).  
            2. One or more **tables** produced by earlier agents (e.g., `sql_query_initiator`, `data_aggregator`).

            Your mission is to **uncover both the obvious and the hidden** in the data—don't just restate what's in the rows, but perform the necessary calculations to reveal deeper trends, anomalies, or impacts.

            ---

            ## Step-by-Step Reasoning

            1. **Interpret** the user's question in full.  
            2. **Decompose** it into atomic sub-questions or metrics to compute (e.g., "What's the average lead time?" , "How did expedited shipping affect costs?").  
            3. **Examine** every table provided—consider relationships, joins, and cross-table comparisons.  
            4. **Perform calculations** (differences, ratios, averages, growth rates, correlations, etc.) to surface insights that aren't immediately visible.  
            5. **Validate** that every conclusion is directly supported by the data; do not introduce unsupported assumptions.

            ---

            ## Some Examples of Thinking:

            Q: Suggest supplier for ITM-2 and ITM-3 procurement plan, for a factory in US location. Consider latest tariff impact for supplier's shipping from location India and China to US, considering US has increased the tariff on China to 35% and India to 30%

            Thought process: Here, user is seeking an alternate supplier for specified Items, they are asking to consider tariffs on China and India, but that doesn't mean that they want suppliers only from China or India, infact they want you to look at all possible suppliers check the overall impact on all suppliers for tariffs and then calculate cost after impact. So a supplier from USA might be best or based on tariff change if the cost comes down then that particular country's supplier might be the best.



            **Q: Suggest options to expedite existing open purchase order (PO-103916) with cost/lead time impact:**

            **Thought Process: Maybe you can look to expedite by switching from sea to air transportation, and hence make joins accordingly for that specific supplier.**
            
            ---

            ## Output Requirements

            You MUST Produce at least one markdown table. But, you may produce **multiple table-insight pairs** to address each sub-query thoroughly. Follow this pattern **for each sub-question**:

            1. **User Requirements** [Never Skip]
            - Enlist the exact user requirements here, these are important details
            - This helps user to track how you came up with the answer (increases accountability)


            2. **Markdown Table** [Never Skip] 
            - Use **standard Markdown table syntax** (no fenced code block).  
            - Clean or rename column headers for readability.
            - Only select useful columns that are contributing to final answer or ones that satisfy the main user query.
            - Only select unique and useful rows after careful consideration, this is essential to reduce user frustration.
            - Include any new calculated columns (e.g., `% change`, `variance`, `impact_score`).  

            3. **Analytical Insight (≥ 100 words)**  
            - Place **immediately after** its corresponding table.  
            - Grounded entirely in the supplied data and your calculations.  
            - Highlight patterns, anomalies, comparisons, and their business or operational implications.  
            - Reference specific table rows or calculated values to justify each point.
            - These insights should be in bulleted format ONLY.

            Repeat the "table → insight" sequence until **every** sub-query has been answered.


            Finally:
            Segue smoothly into Asking if the user has any other questions, maybe you can give some possible follow-up questions like drafting a PO, sending out an email regarding a drafted po.
            Think intelligently and map follow-up questions according to your answer and situation.

            ---

            ## Error & Data-Gap Handling

            🚫 **If data is missing or insufficient:**  
            - Respond with:  
            > "A meaningful report cannot be generated due to lack of complete data."  
            - **Do not** speculate or fill gaps with external knowledge.

            ---

            ## Behavior Checklist

            ✅ **Do**  
            - Analyze **all** tables and cross-reference them.  
            - Break the query into sub-questions and compute each as needed.  
            - Produce one or more Markdown tables, each followed by a detailed narrative insight.  

            🚫 **Do Not**  
            - Omit any provided table.  
            - Make unsupported assumptions or hallucinate data.  
            - Skip calculations or limit yourself to surface-level observations.

            You are now ready to receive a query from `you` and all associated tables. Produce your "table → insight" series in one concise, data-grounded response.

            """
        )

        # Register Panama Canal functions with appropriate agents
        register_function(
            get_delayed_shipments_to_east_coast,
            caller=panama_analysis_agent,
            executor=panama_analysis_agent,
            name="get_delayed_shipments_to_east_coast",
            description="PANAMA CANAL ANALYSIS: Pull shipments heading to US East Coast ports (Port Georgia, Port New York, Port Boston) that are delayed due to Panama Canal slowdown. Use this when user mentions 'Panama Canal', 'canal slowdown', 'East Coast delays', 'port delays', or supply chain disruptions affecting East Coast shipments. Default delay is 15 days.",
        )

        register_function(
            recommend_container_rerouting,
            caller=panama_analysis_agent,
            executor=panama_analysis_agent,
            name="recommend_container_rerouting",
            description="PANAMA CANAL REROUTING: Recommend container rerouting using structured delayed shipments data. REQUIRED PARAMETER: delayed_shipments_data (dict) - output from get_delayed_shipments_to_east_coast function. Optional: min_dos_threshold (int, default 15). You MUST pass the complete delayed_shipments_data dict from the previous function call.",
        )

        register_function(
            calculate_financial_impact_and_recommendation,
            caller=supply_risk_agent,
            executor=supply_risk_agent,
            name="calculate_financial_impact_and_recommendation",
            description="PANAMA CANAL FINANCIAL ANALYSIS: Calculate potential lost sales using structured delayed shipments data. REQUIRED PARAMETER: delayed_shipments_data (dict) - structured output from panama_analysis_agent containing delayed_items, total_value_at_risk, affected_dc, and summary_stats. Optional: rerouting_data (dict) - rerouting cost analysis. You MUST extract and pass the delayed_shipments_data from panama_analysis_agent's function results.",
        )

        you = UserProxyAgent(
            "you",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get(
                "content", "").find("TERMINATE") >= 0,
            max_consecutive_auto_reply=0
        )

        agent_list = [
            you,
            panama_analysis_agent,
            supply_risk_agent,
            optibuy_agent
        ]

        transitions_list = {
            you: [panama_analysis_agent, optibuy_agent],
            panama_analysis_agent: [panama_analysis_agent, supply_risk_agent],
            supply_risk_agent: [supply_risk_agent, optibuy_agent],
            optibuy_agent: [optibuy_agent, you]
        }

        group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=15,  # Increased for comprehensive analysis
            allowed_or_disallowed_speaker_transitions=transitions_list,
            speaker_transitions_type="allowed"
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list_gpt_4o_mini},
        )

        chat_result = agent_list[0].initiate_chat(
            group_chat_manager,
            message="**"+final_query+"**\n\n" +
            datetime.now().strftime("Today's Date is %d-%b-%Y"),
            summary_method="last_msg"
        )

        orchestration_mssg = [{
            "content": "Analyzing Panama Canal delay impacts and rerouting options. Gathering comprehensive data...",
            "role": "assistant",
            "name": "optibuy_agent"
        }]

        # Clean the chat history before adding it
        cleaned_chat = clean_agent_messages(chat_result.chat_history[1:])
        orchestration_mssg.extend(cleaned_chat)

        # orchestration_mssg.extend(chat_result.chat_history[1:])

        return_dict = {
            'chat_history': orchestration_mssg,
            'chat_summary': chat_result.summary,
            'total_time': time.time()-start_time
        }
        print(json.dumps(return_dict, indent=4))

    except Exception as err:
        print(f"Panama Canal Workflow Error: {err}")
        return_dict = {
            'chat_history': None,
            'chat_summary': "error while executing the Panama Canal analysis workflow",
            'total_time': time.time()-start_time
        }
    return return_dict


# === 2. Create a function registry ===
function_registry = {
    "expedite_supply_workflow": expedite_supply_workflow,
    "tariff_impact_workflow": tariff_impact_workflow,
    "route_disruption_workflow": route_disruption_workflow,
    "draft_po_workflow": draft_po_workflow,
    "send_email_workflow": send_email_workflow,
    "panama_canal_workflow": panama_canal_workflow,
    "extract_invoice_details_workflow": extract_invoice_details_workflow,
    "seek_supplier_correction_email_workflow": seek_supplier_correction_email_workflow,
    "read_pr_emails_workflow": read_pr_emails_workflow,
    "send_pr_to_approver_email_workflow": send_pr_to_approver_email_workflow,
    "pr_pending_workflow": pr_pending_workflow,
    "send_pr_reminder_email_workflow": send_pr_reminder_email_workflow,
    "calculate_pr_schedule_changes_workflow": calculate_pr_schedule_changes_workflow
}


@app.post("/flag-runs")
def flag_runs(request: dict):

    print(request['reason'])

    with open('flagged_runs.json', 'r') as f:
        flagged_runs = json.load(f)

    print(type(request))

    flagged_runs.append(request)
    flagged_runs_resp = json.dumps(flagged_runs, indent=4)
    with open("flagged_runs.json", "w") as outfile:
        outfile.write(flagged_runs_resp)

    return {"code": "Success"}


@app.get("/flagged-runs")
def flagged_runs():
    with open('flagged_runs.json', 'r') as f:
        flagged_runs = json.load(f)

    return flagged_runs


@app.post("/panama-canal-analysis")
def panama_canal_analysis(request: PanamaCanalQuery):
    """
    Analyze Panama Canal delay impacts and provide recommendations.

    Args:
        request: PanamaCanalQuery with affected_dc, delay_days, and analysis_type

    Returns:
        Analysis results and recommendations
    """
    try:
        affected_dc = request.affected_dc
        delay_days = request.delay_days
        analysis_type = request.analysis_type

        results = {}

        if analysis_type == "delayed_shipments" or analysis_type == "full":
            results["delayed_shipments"] = get_delayed_shipments_to_east_coast(
                affected_dc, delay_days)

        if analysis_type == "stockout_risk" or analysis_type == "full":
            # Use structured data approach instead of analyze_stockout_risk_by_dc
            delayed_data = get_delayed_shipments_to_east_coast(
                affected_dc, delay_days)
            results["stockout_risk"] = calculate_financial_impact_and_recommendation(
                delayed_data)

        if analysis_type == "rerouting" or analysis_type == "full":
            delayed_data = get_delayed_shipments_to_east_coast(
                affected_dc, delay_days)
            results["rerouting_recommendations"] = recommend_container_rerouting(
                delayed_data)

        if analysis_type == "cost_benefit" or analysis_type == "full":
            delayed_data = get_delayed_shipments_to_east_coast(
                affected_dc, delay_days)
            rerouting_data = recommend_container_rerouting(delayed_data)
            results["cost_benefit_analysis"] = calculate_financial_impact_and_recommendation(
                delayed_data, rerouting_data)

        # Create comprehensive summary for full analysis
        if analysis_type == "full":
            results["summary"] = f"""
**PANAMA CANAL DELAY - COMPREHENSIVE ANALYSIS SUMMARY**

**Scenario:** {delay_days}-day delays reported for vessels heading to East Coast ports due to Panama Canal work slowdown.

**Key Findings:**
• Impact analysis completed for {affected_dc}
• East Coast shipment delays identified and quantified
• Stockout risk assessment performed for high-selling items
• Container rerouting options evaluated from West Coast ports
• Cost-benefit analysis provides clear recommendation

**Next Steps:**
1. Review detailed analysis below
2. Approve/reject rerouting recommendations
3. Notify carriers and distribution centers of decisions
4. Monitor situation for further developments

---
"""

        return {
            "status": "success",
            "analysis_type": analysis_type,
            "affected_dc": affected_dc,
            "delay_days": delay_days,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Panama Canal analysis failed: {str(e)}")


@app.get("/health", status_code=200)
def health():
    return JSONResponse(content={"status": "ok"})


@app.post("/sendgrid-webhook")
async def sendgrid_webhook(request: Request):
    """
    SendGrid Inbound Parse webhook endpoint to receive PR emails.

    SendGrid Inbound Parse sends emails as form data with the following fields:
    - headers: Email headers
    - text: Plain text body
    - html: HTML body
    - from: Sender email
    - to: Recipient email
    - subject: Email subject
    - envelope: SMTP envelope information
    - charsets: Character encoding information
    - SPF: SPF verification result

    To set up SendGrid Inbound Parse:
    1. Go to SendGrid Dashboard > Settings > Inbound Parse
    2. Add a new hostname or use existing
    3. Set POST URL to: https://your-domain.com/sendgrid-webhook
    4. Configure spam check and other settings as needed
    5. Update your domain's MX records as instructed by SendGrid
    """
    try:
        # Get form data from request
        form_data = await request.form()

        # Extract email details
        subject = form_data.get("subject", "No Subject")
        from_email = form_data.get("from", "unknown@example.com")
        to_email = form_data.get("to", "unknown@example.com")

        # Get email body (prefer HTML, fallback to text)
        html_body = form_data.get("html", "")
        text_body = form_data.get("text", "")
        body = html_body if html_body else text_body

        # Get date from headers if available
        headers = form_data.get("headers", "")
        date = None
        if headers:
            # Try to extract date from headers
            import re
            date_match = re.search(r'Date:\s*(.+)', headers, re.IGNORECASE)
            if date_match:
                date = date_match.group(1).strip()

        # Process and save the email
        email_data = process_incoming_email(
            subject=subject,
            body=body,
            from_email=from_email,
            to_email=to_email,
            date=date
        )

        # Save to JSON file
        success = save_pr_email_to_json(email_data)

        if success:
            print(
                f"✅ PR email received and saved: {subject} from {from_email}")
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Email received and processed",
                    "subject": subject,
                    "from": from_email
                },
                status_code=200
            )
        else:
            print(f"❌ Failed to save PR email: {subject} from {from_email}")
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Email received but failed to save"
                },
                status_code=500
            )

    except Exception as e:
        print(f"❌ Error processing SendGrid webhook: {str(e)}")
        # Still return 200 to SendGrid to prevent retries for malformed requests
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Error processing email: {str(e)}"
            },
            status_code=200
        )
