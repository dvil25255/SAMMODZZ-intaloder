# 🤖 Insta Auto-Poster Bot (SAMMODZZ)

Ye ek advanced Instagram Automation Bot hai jo Telegram ke through control hota hai. Ye kisi bhi public account se posts (Images/Reels) copy karke apne account par automatically upload karta hai.

## ✨ Features
- **Auto-Setup via Telegram:** Bot start hote hi khud Session ID aur Target account puchega.
- **Side-by-Side Logic:** Pehle post download hoti hai, phir turant upload hoti hai (Storage full nahi hota).
- **Anti-Ban System:** Random time delay (2-4 hrs) aur upload se pehle random wait (30-90s) taaki Instagram ko shaq na ho.
- **Duplicate Prevention:** Ek `history.txt` file maintain karta hai taaki ek hi post dobara upload na ho.
- **Live Dashboard:** Telegram par status, total uploads, aur start/pause buttons.

## 🛠️ Requirements
- Python 3.8+
- Railway / VPS / Local Server
- `instagrapi` (Instagram Private API wrapper)
- `python-telegram-bot` (Telegram Bot wrapper)

## ⚙️ Environment Variables (Railway/VPS)
Deploy karne se pehle ye variables set karein:
- `BOT_TOKEN` : Telegram BotFather se mila hua token.
- `ADMIN_ID` : Aapki Telegram Chat ID (jisse bot sirf aap command de sake).

## 🚀 Deployment & Usage
1. Code ko GitHub par push karein.
2. Railway par naya project banayein aur GitHub repo connect karein.
3. Upar diye gaye Environment Variables add karein.
4. Deploy hone ke baad, Telegram par apne bot ko `/start` bhejein.
5. `/setup` command chalayein.
6. Bot aapse `sessionid` mangega (Instagram browser cookies se).
7. Login successful hone par bot target account ka username mangega.
8. Setup complete hote hi bot background me kaam shuru kar dega.

## 🔒 Important Security Note
- `.env` file ya session ID kabhi bhi GitHub par public commit na karein.
- Instagram session ID ek private credential hai. Agar ye leak hota hai, toh koi bhi aapke account ka access le sakta hai.
