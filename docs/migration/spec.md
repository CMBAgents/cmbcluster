# Streamlit to Next.js Migration Specification

This document outlines a migration plan for the existing Streamlit-based frontend to a modern Next.js application. It includes an analysis of the current application, a proposed mapping of components and libraries, and considerations for the backend API.

## 1. Current Application Overview

The current frontend is a multi-page Streamlit application that provides a user interface for managing research computing environments.

### 1.1. Pages and Structure

The application is structured into pages and reusable components:

-   **Main Page (`Main.py`):** The main dashboard for viewing and launching computing environments.
-   **Settings Page (`pages/Settings.py`):** A page for managing user settings, preferences, and storage workspaces.
-   **Components (`frontend/components/`):** The application is well-structured with reusable components for handling API calls (`api_client.py`), authentication (`auth.py`), file management (`storage_file_manager.py`), and UI elements.

### 1.2. Dependencies

The `frontend/requirements.txt` file lists the following key Python dependencies:

| Library | Version | Purpose |
| :--- | :--- | :--- |
| `streamlit` | `>=1.46.0` | Core web framework. |
| `requests` | `==2.31.0` | HTTP client for backend API communication. |
| `pandas` | `==2.1.3` | Data manipulation and analysis. |
| `numpy` | `>=1.26.0` | Numerical computing. |
| `plotly` | `==5.17.0` | Interactive charting. |
| `PyJWT` | `==2.8.0` | JWT token decoding for authentication. |
| `python-dotenv`| `==1.0.0` | Environment variable management. |
| `PyYAML` | `==6.0.1` | YAML parsing. |
| `structlog` | | Structured logging. |

## 2. Streamlit Usage Analysis

The application makes extensive use of the Streamlit library for UI, state management, and control flow.

### 2.1. Widgets and Display Elements

A wide range of Streamlit widgets are used, including:
`st.button`, `st.selectbox`, `st.slider`, `st.text_input`, `st.number_input`, `st.file_uploader`, `st.radio`, `st.checkbox`, `st.form`, `st.form_submit_button`, `st.markdown`, `st.image`, `st.metric`, `st.code`, `st.json`, `st.success`, `st.error`, `st.warning`, `st.info`, `st.progress`, `st.spinner`, `st.download_button`.

### 2.2. Layout and Pages

Layout is handled using `st.columns`, `st.container`, `st.expander`, `st.tabs`, and `st.sidebar`. The application is a multi-page app, with pages defined in the `pages/` directory.

### 2.3. State Management

`st.session_state` is used extensively to manage application state, including:
-   User authentication status and token.
-   UI state (e.g., visibility of components).
-   Data fetched from the backend.
-   User selections and form inputs.

## 3. External Integrations

The frontend integrates with several external systems.

### 3.1. Backend API

The primary integration is with the FastAPI backend, facilitated by the `CMBClusterAPIClient` class in `api_client.py`. This client handles all CRUD operations for environments, storage, and user settings.

### 3.2. Authentication

Authentication is handled via an OAuth 2.0 flow. The user is redirected to an external provider for login and returns to the application with a JWT token.

### 3.3. File I/O

The `StorageFileManager` component manages file uploads and downloads. Files are read into memory in the Streamlit application before being sent to the backend API. This is a potential performance bottleneck for large files.

## 4. Proposed Migration to Next.js

The proposed migration involves rebuilding the frontend using Next.js and the React ecosystem.

### 4.1. Component Mapping

The following table maps the currently used Streamlit components to their proposed Next.js/React equivalents. We recommend using a component library like **Shadcn/ui** which is built on top of Radix UI for accessibility and Tailwind CSS for styling.

| Streamlit Component | Next.js/React Equivalent | Library/Component | Notes |
| :--- | :--- | :--- | :--- |
| `st.set_page_config` | Page metadata | `next/head` or Metadata API | For setting page title, favicon, etc. |
| `st.session_state` | State management | React Context, Zustand, Redux | Zustand is a lightweight and popular choice. |
| `st.button` | Button component | `<button>` element, Shadcn/ui `Button` | Shadcn/ui provides accessible and customizable components. |
| `st.selectbox` | Select/Dropdown | Shadcn/ui `Select` | |
| `st.slider` | Slider component | Shadcn/ui `Slider` | |
| `st.text_input` | Input field | Shadcn/ui `Input` | |
| `st.number_input` | Number input | `<input type="number">`, Shadcn/ui `Input` | |
| `st.file_uploader` | File upload component | `react-dropzone` | A popular library for handling file uploads. |
| `st.radio` | Radio group | Shadcn/ui `RadioGroup` | |
| `st.checkbox` | Checkbox component | Shadcn/ui `Checkbox` | |
| `st.form`, `st.form_submit_button` | Form handling | `react-hook-form` | For managing form state and validation. |
| `st.markdown`, `st.write` | Text/Markdown rendering | `react-markdown` | For rendering markdown content safely. |
| `st.image` | Image component | `next/image` | For optimized image loading. |
| `st.metric` | Metric display | Custom component | A simple component to display a value and a label. |
| `st.code`, `st.json` | Code/JSON display | `react-syntax-highlighter` | For syntax-highlighted code blocks. |
| `st.success`, `st.error`, `st.warning`, `st.info` | Toast/Alert notifications | `sonner`, `react-hot-toast` | For displaying non-blocking notifications. |
| `st.progress` | Progress bar | Shadcn/ui `Progress` | |
| `st.spinner` | Loading spinner | `lucide-react` (e.g., `Loader` icon) | Or any other SVG icon library. |
| `st.balloons` | Fun animation | `canvas-confetti` | For celebratory animations. |
| `st.columns`, `st.container` | Layout | CSS Flexbox/Grid, Tailwind CSS | Modern CSS is sufficient for creating complex layouts. |
| `st.expander` | Accordion/Collapsible | Shadcn/ui `Accordion` | |
| `st.tabs` | Tabs component | Shadcn/ui `Tabs` | |
| `st.sidebar` | Sidebar layout | Custom component with CSS | A common layout pattern, easy to implement with CSS. |
| `st.rerun()`, `st.stop()` | Control flow | State updates, conditional rendering | React's declarative nature handles this differently. |
| `st.download_button` | Download link | `<a>` tag with `download` attribute | File content can be fetched and provided as a data URL. |
| `st.empty()` | Dynamic content | Conditional rendering | Render different components based on state. |
| `st.query_params` | URL query parameters | `next/navigation` (`useSearchParams`) | For reading and manipulating URL query parameters. |
| `plotly` charts | Interactive charts | `plotly.js` or `react-plotly.js` | The JavaScript version of the same library. |

### 4.2. State Management

For global state management (e.g., user authentication, session info), a lightweight library like **Zustand** is recommended. For local component state, React's built-in `useState` and `useReducer` hooks will suffice.

### 4.3. Styling

**Tailwind CSS** is recommended for styling, as it integrates well with Next.js and allows for rapid development of modern user interfaces.

## 5. Backend (FastAPI) Considerations

The existing FastAPI backend provides a solid foundation. The Next.js frontend will interact with this backend.

### 5.1. Required Endpoints

The frontend will require a comprehensive set of RESTful endpoints to manage resources. The existing endpoints called by `api_client.py` are a good starting point, but they should be reviewed and formalized. Key functionalities to be covered include:

-   **Authentication:** `/login`, `/token`, `/user/me`, `/logout`.
-   **Environment Management:** CRUD operations for environments.
-   **Storage Management:** CRUD operations for storage buckets and files within them.
-   **User Settings:** Endpoints for managing user preferences and environment variables.
-   **Monitoring:** Endpoints for activity logs and system status.

### 5.2. Identified Gaps and Improvements

-   **Asynchronous Operations:** Long-running operations like `restart_environment` (which currently includes a `time.sleep(3)`) should be made asynchronous. The API should immediately return a task ID, and the frontend should poll a status endpoint to get updates.
-   **Streaming File I/O:** For better performance and memory efficiency, the backend should support streaming file uploads and downloads.
-   **Security:** The practice of skipping JWT signature verification in `auth.py` must be addressed in a production environment. The backend should be responsible for validating all tokens.

## 6. Migration Strategy & Next Steps

1.  **Setup Next.js Project:** Initialize a new Next.js project with TypeScript, ESLint, Prettier, and Tailwind CSS.
2.  **Implement Authentication:** Build the login page and authentication flow, connecting to the existing backend auth endpoints.
3.  **Develop Core Layout:** Create the main application layout, including the sidebar and navigation.
4.  **Migrate Pages Incrementally:**
    -   Start with the `Settings` page, as it has a variety of forms and data display elements.
    -   Then, migrate the main `Environments` dashboard.
5.  **Develop Reusable Components:** Build a library of reusable React components based on the mapping in section 4.1.
6.  **Refactor Backend (as needed):** Address the gaps identified in section 5.2, particularly the asynchronous operations.
7.  **Testing:** Thoroughly test the new frontend to ensure feature parity and a smooth user experience.
