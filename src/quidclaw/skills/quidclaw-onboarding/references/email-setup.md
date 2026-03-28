# Email Setup (Optional)

After showing the user the inbox folder, offer email integration:

"By the way — would you like me to set up a dedicated email address for you? You can forward your bank statements and bills there, and I'll automatically pick them up and process them. It's completely optional."

If they say yes:

1. Explain: "I'll use a service called AgentMail to create a mailbox for you. It's a third-party email service — I want to be upfront about that. Your emails go directly to their servers, and I fetch them from there. I don't store any credentials beyond the API key, and I can only see the emails sent to this specific address."

2. Ask: "Do you have an AgentMail account? If not, you can create one for free at console.agentmail.to — it takes about a minute. The free plan gives you 3 mailboxes and 3,000 emails per month, which is plenty."

3. Once they provide the API key, ask: "What name would you like for your email address? For example, 'thorb-cfo' would give you thorb-cfo@agentmail.to. Or I can generate a random one for you."

4. Run the setup:
   ```
   quidclaw add-source my-email --provider agentmail --api-key <their_key> --inbox-id <chosen_name>@agentmail.to
   ```
   If they didn't specify a name, omit --inbox-id and one will be generated.

5. Confirm: "Done! Your email is {address}. You can now go to your banks and set up bill forwarding to this address. Whenever a new bill arrives, I'll pick it up automatically."

6. Save the email address to `notes/profile.md` under a new "## Data Sources" section.

If they say no:
  "No problem! You can always set this up later. Just tell me 'set up email' whenever you're ready."
  Record in `notes/profile.md` under `## Data Sources`: "Email integration: declined ({reason if given}). Can set up later."

## Privacy Requirements

- Explicitly name AgentMail as a third-party service
- Clarify that the AI cannot see the user's other emails — only those sent to this specific address
- Explain that the API key is stored locally in `.quidclaw/config.yaml`
- Never pressure the user — this is entirely optional
