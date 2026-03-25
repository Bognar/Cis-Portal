<img width="1223" height="443" alt="image" src="https://github.com/user-attachments/assets/f4938ab9-6228-4478-8c45-4eee40f1a11e" />

CIS Report Generator
The app was create to help me make clean report by using information from CIS CSAT portal. After you finish the report and get scores per safeguard, you can then build nice report with custom features.
Feature list:
Text bolding can be added to any text box: ***boldtext** 
Image imports for all sections including cover page and each of major sections.
Export work into json file and import later if needed.
Generating report into PDF format.

Please find example report in root.

Installing and running the app on linux
```
mkdir yourprojectname
cd jourprojectname
python3 -m venv venv
source venv/bin/activate
Git clone https://github.com/Bognar/Cis-Portal.git
cd Cis-Portal
pip install streamlit fpdf2
streamlit run app.py
```
Installing and running app on windows
```
mkdir yourprojectname
cd yourprojectname
python -m venv venv
.\venv\Scripts\activate
git clone https://github.com/Bognar/Cis-Portal.git
cd Cis-Portal
pip install streamlit fpdf2
streamlit run app.py
```
Open localhost:8501

<img width="371" height="53" alt="image" src="https://github.com/user-attachments/assets/91d13e3d-7254-4607-871a-37774456ecaa" />
