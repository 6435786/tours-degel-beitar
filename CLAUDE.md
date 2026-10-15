# כללים קבועים למאגר הזה — חובה לכל עבודה

המאגר הזה **ציבורי**: כל קובץ שעולה אליו גלוי לכל העולם, וגם אחרי מחיקה הוא נשאר בהיסטוריה.

## לפני כל commit / push
1. **אסור להעלות שום דבר בלי אישור מפורש של שלמה.** לפני כל commit ולפני כל push מציגים לו:
   - רשימה מלאה ומדויקת של הקבצים שייכנסו (`git status`, `git diff --cached --stat`),
   - במילים פשוטות: מה השתנה בכל קובץ.
   ומחכים לתשובה "מאשר". בלי אישור — לא מעלים, גם לא "רק תיקון קטן".
2. **אסור** `git add -A`, `git add .`, `git add --all` או `git commit -a`. מוסיפים קבצים **בשמם בלבד**.
3. **אסור להעלות קבצי נתונים**: CSV, אקסל (xlsx/xls), Word, PDF, ZIP, ייצוא גיליונות, קבצי `tmp_*`, וכל קובץ עם שמות, תעודות זהות, טלפונים או כתובות של אנשים.

## קבצי עבודה
4. לא שומרים בתיקיית המאגר קבצים של פרויקטים אחרים (סמינרים, מתנ"ס, תקציבים וכו').
   קבצי עבודה זמניים נשמרים **מחוץ** לתיקיית המאגר.
5. אם מגלים בתיקייה קבצים שלא שייכים לאתר — לא נוגעים בהם ולא מעלים אותם; מדווחים לשלמה.

## Rules (English summary for the assistant)
- Public repo. Never commit or push without showing the owner the exact file list and a plain-language summary, and receiving explicit approval.
- Stage files by explicit path only; never `git add -A` / `git add .` / `git commit -a`.
- Never commit data files (csv, xlsx, xls, docx, pdf, zip, sheet exports, tmp_*) or anything containing personal data.
- Keep scratch/work files of other projects outside this repository.
