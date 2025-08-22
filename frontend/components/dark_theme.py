"""
Production-Grade Dark Theme Styles for CMBCluster
Professional, modern design with excellent usability and accessibility
"""

DARK_THEME_CSS = """
<style>
    /* Import Google Fonts for professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global color palette - Professional dark theme */
    :root {
        --bg-primary: #0F1419;
        --bg-secondary: #1A1F2E;
        --bg-tertiary: #252B3A;
        --bg-accent: #2D3748;
        
        --text-primary: #FFFFFF;
        --text-secondary: #E2E8F0;
        --text-muted: #A0AEC0;
        --text-disabled: #718096;
        
        --accent-primary: #4299E1;
        --accent-secondary: #3182CE;
        --accent-light: #63B3ED;
        
        --success: #48BB78;
        --warning: #ED8936;
        --error: #F56565;
        --info: #4299E1;
        
        --border-primary: #2D3748;
        --border-secondary: #4A5568;
        --border-accent: #4299E1;
        
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04);
        
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
    }
    
    /* Main application styling */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #151A26 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        line-height: 1.6;
    }
    
    /* Typography enhancements */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.025em;
    }
    
    h1 { font-size: 2.5rem; margin-bottom: 1.5rem; }
    h2 { font-size: 2rem; margin-bottom: 1.25rem; }
    h3 { font-size: 1.5rem; margin-bottom: 1rem; }
    h4 { font-size: 1.25rem; margin-bottom: 0.75rem; }
    
    p, .stMarkdown {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.7;
    }
    
    /* Professional card designs */
    .env-card {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-lg);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .env-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-light));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .env-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-xl);
        border-color: var(--border-accent);
    }
    
    .env-card:hover::before {
        opacity: 1;
    }
    
    .env-card h4 {
        color: var(--text-primary);
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .env-card p {
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    .env-card strong {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .env-card a {
        color: var(--accent-primary);
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s ease;
    }
    
    .env-card a:hover {
        color: var(--accent-light);
        text-decoration: underline;
    }
    
    /* Status cards with modern design */
    .status-card {
        background: linear-gradient(145deg, rgba(72, 187, 120, 0.1), rgba(72, 187, 120, 0.05));
        border: 1px solid rgba(72, 187, 120, 0.3);
        border-left: 4px solid var(--success);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(10px);
    }
    
    .status-card h4 {
        color: var(--success);
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .warning-card {
        background: linear-gradient(145deg, rgba(237, 137, 54, 0.1), rgba(237, 137, 54, 0.05));
        border: 1px solid rgba(237, 137, 54, 0.3);
        border-left: 4px solid var(--warning);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(10px);
    }
    
    .warning-card h4 {
        color: var(--warning);
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .error-card {
        background: linear-gradient(145deg, rgba(245, 101, 101, 0.1), rgba(245, 101, 101, 0.05));
        border: 1px solid rgba(245, 101, 101, 0.3);
        border-left: 4px solid var(--error);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(10px);
    }
    
    .error-card h4 {
        color: var(--error);
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Settings cards with premium feel */
    .settings-card {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .settings-card:hover {
        box-shadow: var(--shadow-lg);
        border-color: var(--border-secondary);
    }
    
    .settings-card h4 {
        color: var(--text-primary);
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .info-card {
        background: linear-gradient(135deg, rgba(66, 153, 225, 0.15) 0%, rgba(66, 153, 225, 0.05) 100%);
        border: 1px solid rgba(66, 153, 225, 0.3);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-md);
        backdrop-filter: blur(10px);
    }
    
    .info-card h4 {
        color: var(--accent-primary);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    /* Modern form elements */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
        outline: none !important;
    }
    
    .stSelectbox > div > div > select {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stSelectbox > div > div > select:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
    }
    
    .stNumberInput > div > div > input {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
    }
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(145deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
        background: linear-gradient(145deg, var(--accent-light), var(--accent-primary)) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary button style */
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--border-secondary) !important;
        color: var(--text-secondary) !important;
    }
    
    .stButton > button[data-baseweb="button"][kind="secondary"]:hover {
        background: var(--bg-tertiary) !important;
        border-color: var(--border-accent) !important;
        color: var(--text-primary) !important;
    }
    
    /* Progress bars */
    .stProgress .st-bo {
        background-color: var(--bg-tertiary) !important;
        border-radius: var(--radius-sm) !important;
    }
    
    .stProgress .st-bp {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-light)) !important;
        border-radius: var(--radius-sm) !important;
    }
    
    /* Checkbox and radio styling */
    .stCheckbox > label,
    .stRadio > label {
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Slider styling */
    .stSlider > div > div {
        background-color: var(--bg-tertiary) !important;
    }
    
    .stSlider > div > div > div > div {
        background-color: var(--accent-primary) !important;
    }
    
    /* Alert messages with modern design */
    .stAlert > div {
        background: linear-gradient(145deg, rgba(66, 153, 225, 0.1), rgba(66, 153, 225, 0.05)) !important;
        border: 1px solid rgba(66, 153, 225, 0.3) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSuccess > div {
        background: linear-gradient(145deg, rgba(72, 187, 120, 0.1), rgba(72, 187, 120, 0.05)) !important;
        border: 1px solid rgba(72, 187, 120, 0.3) !important;
        color: var(--text-primary) !important;
    }
    
    .stWarning > div {
        background: linear-gradient(145deg, rgba(237, 137, 54, 0.1), rgba(237, 137, 54, 0.05)) !important;
        border: 1px solid rgba(237, 137, 54, 0.3) !important;
        color: var(--text-primary) !important;
    }
    
    .stError > div {
        background: linear-gradient(145deg, rgba(245, 101, 101, 0.1), rgba(245, 101, 101, 0.05)) !important;
        border: 1px solid rgba(245, 101, 101, 0.3) !important;
        color: var(--text-primary) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%) !important;
        border-right: 1px solid var(--border-primary) !important;
    }
    
    /* Tab styling with modern design */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.25rem !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
    }
    
    /* Metric styling */
    .metric-container {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary)) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    /* Code blocks */
    code {
        background: var(--bg-tertiary) !important;
        color: var(--accent-light) !important;
        font-family: 'JetBrains Mono', 'Monaco', 'Menlo', monospace !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem !important;
    }
    
    pre {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        padding: 1rem !important;
        overflow-x: auto !important;
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border-radius: var(--radius-xl);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.75rem;
        box-shadow: 0 0 8px currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .status-running { 
        background-color: var(--success);
        color: var(--success);
    }
    
    .status-pending { 
        background-color: var(--warning);
        color: var(--warning);
    }
    
    .status-failed { 
        background-color: var(--error);
        color: var(--error);
    }
    
    .status-unknown { 
        background-color: var(--text-disabled);
        color: var(--text-disabled);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
        border-radius: var(--radius-sm);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-secondary);
        border-radius: var(--radius-sm);
        transition: background 0.2s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--border-accent);
    }
    
    /* Loading spinners */
    .stSpinner > div {
        border-color: var(--accent-primary) transparent var(--accent-primary) transparent !important;
    }
    
    /* Divider styling */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border-primary), transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* Table styling */
    .stDataFrame {
        background: var(--bg-secondary) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .env-card, .settings-card {
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        h1 { font-size: 2rem; }
        h2 { font-size: 1.75rem; }
        h3 { font-size: 1.5rem; }
    }
    
    /* Accessibility improvements */
    .stButton > button:focus,
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        outline: 2px solid var(--accent-primary) !important;
        outline-offset: 2px !important;
    }
    
    /* Print styles */
    @media print {
        .stApp {
            background: white !important;
            color: black !important;
        }
        
        .env-card, .settings-card {
            border: 1px solid #ccc !important;
            box-shadow: none !important;
        }
    }
    
    /* File Upload Specific Styles */
    .file-upload-container {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border: 2px dashed var(--border-primary);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .file-upload-container:hover {
        border-color: var(--accent-primary);
        background: linear-gradient(145deg, var(--bg-tertiary), var(--bg-accent));
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .file-upload-container.drag-over {
        border-color: var(--accent-light);
        background: linear-gradient(145deg, rgba(66, 153, 225, 0.1), rgba(66, 153, 225, 0.05));
        box-shadow: 0 0 20px rgba(66, 153, 225, 0.3);
    }
    
    .file-upload-icon {
        font-size: 3rem;
        color: var(--accent-primary);
        margin-bottom: 1rem;
        opacity: 0.8;
        transition: all 0.3s ease;
    }
    
    .file-upload-container:hover .file-upload-icon {
        opacity: 1;
        transform: scale(1.1);
    }
    
    .file-upload-text {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .file-upload-subtext {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    
    .file-upload-button {
        background: linear-gradient(145deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 2rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    .file-upload-button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(145deg, var(--accent-light), var(--accent-primary)) !important;
    }
    
    /* File Card Styles */
    .file-card {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .file-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-light));
    }
    
    .file-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--border-accent);
    }
    
    .file-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .file-card-title {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .file-card-type {
        background: linear-gradient(145deg, var(--accent-primary), var(--accent-secondary));
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: var(--radius-sm);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .file-card-meta {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .file-card-meta-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .file-card-meta-label {
        color: var(--text-muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }
    
    .file-card-meta-value {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .file-card-actions {
        display: flex;
        gap: 0.75rem;
        margin-top: 1rem;
    }
    
    .file-card-action-btn {
        background: transparent !important;
        border: 1px solid var(--border-secondary) !important;
        color: var(--text-secondary) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .file-card-action-btn:hover {
        background: var(--bg-accent) !important;
        border-color: var(--border-accent) !important;
        color: var(--text-primary) !important;
        transform: translateY(-1px) !important;
    }
    
    .file-card-action-btn.danger {
        border-color: rgba(245, 101, 101, 0.5) !important;
        color: var(--error) !important;
    }
    
    .file-card-action-btn.danger:hover {
        background: rgba(245, 101, 101, 0.1) !important;
        border-color: var(--error) !important;
        color: var(--error) !important;
    }
    
    /* File Validation Styles */
    .file-validation-error {
        background: linear-gradient(145deg, rgba(245, 101, 101, 0.1), rgba(245, 101, 101, 0.05));
        border: 1px solid rgba(245, 101, 101, 0.3);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin: 1rem 0;
        color: var(--error);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .file-validation-success {
        background: linear-gradient(145deg, rgba(72, 187, 120, 0.1), rgba(72, 187, 120, 0.05));
        border: 1px solid rgba(72, 187, 120, 0.3);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin: 1rem 0;
        color: var(--success);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .file-validation-warning {
        background: linear-gradient(145deg, rgba(237, 137, 54, 0.1), rgba(237, 137, 54, 0.05));
        border: 1px solid rgba(237, 137, 54, 0.3);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin: 1rem 0;
        color: var(--warning);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    /* File Upload Progress */
    .file-upload-progress {
        width: 100%;
        height: 6px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .file-upload-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-light));
        border-radius: var(--radius-sm);
        transition: width 0.3s ease;
        animation: progress-pulse 2s infinite;
    }
    
    @keyframes progress-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* File Type Icons */
    .file-type-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    
    .file-type-icon.json {
        color: #FFA500;
    }
    
    .file-type-icon.gcp {
        color: #4285F4;
    }
    
    .file-type-icon.config {
        color: #6C757D;
    }
    
    /* Empty State */
    .file-empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-muted);
    }
    
    .file-empty-state-icon {
        font-size: 4rem;
        color: var(--text-disabled);
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .file-empty-state-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }
    
    .file-empty-state-text {
        font-size: 0.95rem;
        color: var(--text-muted);
        line-height: 1.6;
    }
    
    /* File Upload Modal/Dialog */
    .file-upload-modal {
        background: linear-gradient(145deg, var(--bg-secondary), var(--bg-tertiary));
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-xl);
        backdrop-filter: blur(20px);
    }
    
    .file-upload-modal-header {
        padding: 1.5rem 2rem 0;
        border-bottom: 1px solid var(--border-primary);
    }
    
    .file-upload-modal-title {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    .file-upload-modal-content {
        padding: 2rem;
    }
    
    /* Responsive File Upload */
    @media (max-width: 768px) {
        .file-upload-container {
            padding: 1.5rem 1rem;
        }
        
        .file-card {
            padding: 1rem;
        }
        
        .file-card-actions {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .file-card-action-btn {
            width: 100%;
        }
        
        .file-card-meta {
            flex-direction: column;
            gap: 0.75rem;
        }
    }
    
    /* Animation for file operations */
    .file-fade-in {
        animation: fadeIn 0.3s ease-in-out;
    }
    
    .file-fade-out {
        animation: fadeOut 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
</style>
"""
