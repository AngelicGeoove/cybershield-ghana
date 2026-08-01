from flask import Blueprint, render_template
from flask_login import login_required

awareness_bp = Blueprint('awareness', __name__)

@awareness_bp.before_request
@login_required
def require_login():
    pass

TOPICS = {
    'phishing': {
        'title': 'Phishing',
        'what': 'Phishing is a type of scam where attackers pretend to be a trusted entity (bank, company, government) to trick you into revealing sensitive information like passwords or financial details.',
        'warning_signs': [
            'Unexpected emails or messages asking for personal information',
            'Urgent language pressuring you to act immediately',
            'Suspicious links or URLs that look slightly wrong',
            'Generic greetings like "Dear Customer" instead of your name',
            'Requests for passwords, PINs, or OTPs'
        ],
        'what_to_do': [
            'Do not click links in suspicious messages',
            'Verify the sender by contacting them through official channels',
            'Report the phishing attempt to the CSA',
            'Use bookmarks for important websites instead of clicking links'
        ],
        'what_not_to_do': [
            'Do not provide passwords or PINs via email or message',
            'Do not click suspicious links',
            'Do not reply to phishing messages',
            'Do not enter credentials on unsecured websites'
        ],
        'how_to_report': 'Forward phishing emails to report@csa.gov.gh or use the Report via Email feature in this app.'
    },
    'mobile-money-scams': {
        'title': 'Mobile Money Scams',
        'what': 'Mobile money scams involve fraudsters targeting mobile money users through fake promotions, scam calls, or impersonation of legitimate services to steal funds.',
        'warning_signs': [
            'Unexpected calls claiming to be from your mobile money provider',
            'Promises of easy money or high returns',
            'Requests to share your PIN or OTP',
            'Messages saying your account is locked and you need to act fast',
            'Suspicious phone numbers or short codes'
        ],
        'what_to_do': [
            'Never share your PIN or OTP with anyone',
            'Contact your mobile money provider through official channels',
            'Report the scam to the CSA and your mobile money provider',
            'Block and report suspicious numbers'
        ],
        'what_not_to_do': [
            'Never share your PIN or OTP',
            'Do not respond to calls asking for verification codes',
            'Do not send money to strangers promising returns',
            'Do not ignore warnings from your provider'
        ],
        'how_to_report': 'Call the CSA\'s official number or use WhatsApp reporting in this app.'
    },
    'social-media-scams': {
        'title': 'Social Media Scams',
        'what': 'Social media scams use fake profiles, impersonation, or fraudulent offers on social platforms to deceive users into giving money or personal information.',
        'warning_signs': [
            'New accounts impersonating real people or organisations',
            'Unusual friend requests or messages from strangers',
            'Promises of prizes or giveaways in exchange for personal info',
            'Romance scams building emotional connections quickly',
            'Fake job offers or investment opportunities'
        ],
        'what_to_do': [
            'Verify identities before engaging with strangers',
            'Report fake accounts to the platform',
            'Do not share personal information with unknown contacts',
            'Report social media scams to the CSA'
        ],
        'what_not_to_do': [
            'Do not send money to online strangers',
            'Do not share personal details with unverified accounts',
            'Do not click links from unknown sources',
            'Do not ignore warning signs of impersonation'
        ],
        'how_to_report': 'Report through WhatsApp or the CSA online form.'
    },
    'online-shopping-scams': {
        'title': 'Online Shopping Scams',
        'what': 'Online shopping scams involve fake websites or sellers that take payment but never deliver goods or services.',
        'warning_signs': [
            'Prices that seem too good to be true',
            'New websites with no reviews or reputation',
            'Requests for unusual payment methods',
            'Poor website design or grammar errors',
            'No clear contact information or return policy'
        ],
        'what_to_do': [
            'Research the seller before purchasing',
            'Use secure payment methods with buyer protection',
            'Check for reviews and ratings from other customers',
            'Report the scam to the CSA'
        ],
        'what_not_to_do': [
            'Do not pay via bank transfer to unknown sellers',
            'Do not ignore red flags about a website',
            'Do not share payment details on unsecured sites',
            'Do not assume a website is legitimate based on its appearance alone'
        ],
        'how_to_report': 'Report via email to the CSA or use the in-app reporting feature.'
    },
    'investment-scams': {
        'title': 'Investment Scams',
        'what': 'Investment scams promise high returns with low risk to trick you into handing over money that is never returned.',
        'warning_signs': [
            'Guaranteed high returns with no or low risk',
            'Urgency to invest immediately',
            'Pressure from "investment advisors"',
            'Complex strategies you do not understand',
            'Lack of proper licensing or registration'
        ],
        'what_to_do': [
            'Verify investment opportunities with the SEC Ghana or relevant authority',
            'Never invest money you cannot afford to lose',
            'Get independent financial advice',
            'Report investment scams to the CSA'
        ],
        'what_not_to_do': [
            'Do not invest based on promises of guaranteed returns',
            'Do not share financial details with unverified advisors',
            'Do not send money based on social media offers',
            'Do not ignore warning signs of fraud'
        ],
        'how_to_report': 'Report to the CSA through the reporting channels in this app.'
    },
    'account-takeover': {
        'title': 'Account Takeover',
        'what': 'Account takeover occurs when an unauthorised person gains access to your online accounts, potentially stealing your data, money, or identity.',
        'warning_signs': [
            'Unusual activity on your accounts',
            'Passwords no longer working',
            'Unknown devices logged into your accounts',
            'Emails or notifications about logins you did not make',
            'Changes to account settings you did not make'
        ],
        'what_to_do': [
            'Change your passwords immediately',
            'Enable two-factor authentication',
            'Check account activity logs',
            'Contact your bank and relevant service providers',
            'Report to the CSA'
        ],
        'what_not_to_do': [
            'Do not ignore signs of account compromise',
            'Do not reuse passwords across accounts',
            'Do not share account credentials',
            'Do not click links in suspicious account alerts'
        ],
        'how_to_report': 'Report to the CSA via email or WhatsApp.'
    },
    'password-security': {
        'title': 'Password Security',
        'what': 'Good password hygiene is essential for protecting your online accounts and personal information from unauthorised access.',
        'warning_signs': [
            'Using the same password across multiple accounts',
            'Using simple or common passwords',
            'Never changing passwords',
            'Sharing passwords with others',
            'Writing passwords down in easily accessible places'
        ],
        'what_to_do': [
            'Use strong, unique passwords for each account',
            'Enable two-factor authentication wherever available',
            'Use a reputable password manager',
            'Change passwords regularly',
            'Never share your passwords with anyone'
        ],
        'what_not_to_do': [
            'Do not use personal information in passwords',
            'Do not share your passwords',
            'Do not reuse passwords across sites',
            'Do not store passwords in plain text'
        ],
        'how_to_report': 'Report password-related incidents to the CSA.'
    },
    'two-factor-authentication': {
        'title': 'Two-Factor Authentication',
        'what': 'Two-factor authentication (2FA) adds an extra layer of security by requiring a second form of verification beyond your password.',
        'warning_signs': [
            'Not having 2FA enabled on important accounts',
            'Receiving authentication codes you did not request',
            'Being unable to access accounts despite knowing the password'
        ],
        'what_to_do': [
            'Enable 2FA on all important accounts',
            'Use authenticator apps rather than SMS when possible',
            'Keep backup codes safe',
            'Never share 2FA codes with anyone'
        ],
        'what_not_to_do': [
            'Do not share your 2FA codes',
            'Do not disable 2FA unless absolutely necessary',
            'Do not rely solely on SMS for 2FA',
            'Do not ignore prompts about unauthorised 2FA attempts'
        ],
        'how_to_report': 'Report 2FA-related fraud to the CSA.'
    },
    'suspicious-links': {
        'title': 'Suspicious Links',
        'what': 'Suspicious links can lead to phishing sites, malware downloads, or other threats that compromise your device and data.',
        'warning_signs': [
            'Links from unknown senders',
            'URLs that look slightly different from the official site',
            'Links promising unexpected rewards or prizes',
            'Shortened URLs from unknown sources',
            'Links in unsolicited emails or messages'
        ],
        'what_to_do': [
            'Hover over links to preview the URL before clicking',
            'Verify the sender before clicking any links',
            'Use link-checking tools to verify URLs',
            'Report suspicious links to the CSA'
        ],
        'what_not_to_do': [
            'Do not click on links from unknown senders',
            'Do not enter credentials after clicking a suspicious link',
            'Do not download files from suspicious links',
            'Do not ignore browser warnings about unsafe sites'
        ],
        'how_to_report': 'Report suspicious links to the CSA.'
    },
    'malware': {
        'title': 'Malware',
        'what': 'Malware is malicious software designed to damage, disrupt, or gain unauthorised access to your device or data.',
        'warning_signs': [
            'Sluggish device performance',
            'Unexpected pop-ups or ads',
            'Unknown programs running',
            'Files being modified or encrypted',
            'Unusual network activity'
        ],
        'what_to_do': [
            'Keep your antivirus software updated',
            'Do not download software from untrusted sources',
            'Regularly update your operating system and apps',
            'Report malware incidents to the CSA'
        ],
        'what_not_to_do': [
            'Do not open attachments from unknown senders',
            'Do not download pirated software',
            'Do not ignore antivirus warnings',
            'Do not try to remove serious malware yourself if it compromises evidence'
        ],
        'how_to_report': 'Report malware incidents to the CSA.'
    },
    'identity-theft': {
        'title': 'Identity Theft',
        'what': 'Identity theft occurs when someone steals your personal information to commit fraud, such as opening accounts or making transactions in your name.',
        'warning_signs': [
            'Accounts you did not open appearing on your credit report',
            'Unexpected bills or collection notices',
            'Missing mail or financial statements',
            'Notifications about breaches of services you use',
            'Credit denial for no apparent reason'
        ],
        'what_to_do': [
            'Freeze your credit immediately',
            'Report to the relevant authorities',
            'Change all your passwords',
            'Monitor your accounts closely',
            'Report to the CSA'
        ],
        'what_not_to_do': [
            'Do not ignore signs of identity theft',
            'Do not share personal documents unnecessarily',
            'Do not provide your details to unverified parties',
            'Do not assume it will resolve itself'
        ],
        'how_to_report': 'Report identity theft to the CSA immediately.'
    },
    'online-blackmail': {
        'title': 'Online Blackmail',
        'what': 'Online blackmail involves threats to share compromising material unless payment or other demands are met.',
        'warning_signs': [
            'Threats to share personal or compromising material',
            'Demand for payment in exchange for not sharing content',
            'Unwanted sexual advances online',
            'Threats across multiple platforms'
        ],
        'what_to_do': [
            'Do not pay or comply with demands',
            'Save all evidence including messages and usernames',
            'Block the person and report to the platform',
            'Report to the CSA immediately'
        ],
        'what_not_to_do': [
            'Do not pay the blackmailer',
            'Do not engage or negotiate with the blackmailer',
            'Do not delete evidence',
            'Do not feel ashamed - this is a crime'
        ],
        'how_to_report': 'Report to the CSA via WhatsApp or the online form.'
    },
    'impersonation': {
        'title': 'Impersonation',
        'what': 'Impersonation involves someone pretending to be you or a trusted person/organisation to deceive others or gain access to your accounts.',
        'warning_signs': [
            'Fake accounts using your name and photos',
            'Friends or family receiving messages from your accounts that you did not send',
            'Someone contacting you pretending to be a known person or organisation',
            'Unauthorised access to your accounts'
        ],
        'what_to_do': [
            'Report fake accounts to the relevant platform',
            'Notify your friends and contacts',
            'Secure your accounts with strong passwords and 2FA',
            'Report impersonation to the CSA'
        ],
        'what_not_to_do': [
            'Do not engage with impersonators',
            'Do not provide information to suspected impersonators',
            'Do not ignore impersonation on social media',
            'Do not share your credentials with anyone'
        ],
        'how_to_report': 'Report impersonation to the CSA.'
    }
}

@awareness_bp.route('/safety')
@login_required
def index():
    return render_template('awareness/index.html', topics=TOPICS)

@awareness_bp.route('/safety/<topic_id>')
@login_required
def topic_detail(topic_id):
    topic = TOPICS.get(topic_id)
    if not topic:
        flash('Topic not found.', 'error')
        return redirect(url_for('awareness.index'))
    return render_template('awareness/topic.html', topic=topic, topic_id=topic_id)