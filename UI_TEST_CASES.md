# CMB Cluster Frontend-Backend Integration Test Plan

## 🎯 Comprehensive UI Test Cases for Next.js → FastAPI Integration

This document provides a complete manual testing guide to verify your Next.js frontend works with your FastAPI backend.

## Quick Integration Test Commands

```bash
# Start backend
cd backend
python main.py

# Start frontend
cd nextjs-frontend  
npm run dev

# Test endpoints
curl -H "Authorization: Bearer dev-token" http://localhost:8000/health
```

---

## 🔐 Authentication Flow Tests

### Test 1: Google OAuth Login
**Expected Backend**: `POST /auth/login` → `GET /auth/callback`
**Frontend Flow**: Click "Sign In" → Google OAuth → Redirect back

**Test Steps:**
1. Navigate to http://localhost:8501
2. Click "Sign In with Google"
3. Complete Google OAuth flow
4. Verify redirect to dashboard with user data

**✅ Success Criteria:**
- User redirected to `/dashboard` 
- User name displayed in header
- JWT token stored in session
- API calls include `Authorization: Bearer <token>` header

**🔍 Debug Checklist:**
- [ ] `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` match in both frontend and backend
- [ ] `NEXTAUTH_URL` matches frontend URL
- [ ] Backend CORS allows frontend domain
- [ ] Session secret keys match

---

## 🚀 Environment Management Tests

### Test 2: Create New Environment
**Backend Endpoint**: `POST /environments`
**Frontend**: Environment page → "Launch Environment"

**Test Payload:**
```json
{
  "cpu_limit": 2.0,
  "memory_limit": "4Gi", 
  "storage_size": "50Gi",
  "storage_id": "storage-123",
  "create_new_storage": false
}
```

**Test Steps:**
1. Go to `/environments`
2. Click "Launch Environment"
3. Select "Standard Research" preset
4. Choose "Use Existing Workspace" 
5. Select a storage option
6. Click "Launch Environment"

**✅ Success Criteria:**
- Loading progress bar appears
- Success notification shows
- New environment appears in list
- Status shows "Pending" then "Running"
- Access URL is clickable

### Test 3: List Environments  
**Backend Endpoint**: `GET /environments/list`
**Frontend**: Auto-refresh every 10 seconds

**Test Steps:**
1. Navigate to `/environments`
2. Wait for data to load
3. Verify environments display correctly
4. Check status badges
5. Verify resource information
6. Wait 10 seconds and observe auto-refresh

**✅ Success Criteria:**
- All environments from backend appear
- Correct status colors (green=running, yellow=pending, red=failed)
- Resource configs display correctly
- Real-time updates work
- Search and filtering work

### Test 4: Environment Actions
**Test Restart:** `DELETE /environments` → `POST /environments`
**Test Stop:** `POST /environments/{id}/stop`
**Test Delete:** `DELETE /environments`

**Test Steps:**
1. Find running environment
2. Click restart button → confirm modal
3. Verify environment restarts
4. Click stop button → confirm modal  
5. Verify environment stops
6. Click delete button → confirm modal
7. Verify environment removed

**✅ Success Criteria:**
- Confirmation modals appear
- Actions complete successfully 
- Environment status updates correctly
- Notifications appear
- List refreshes automatically

---

## 🗄️ Storage Management Tests

### Test 5: List User Storage
**Backend Endpoint**: `GET /storage/list`
**Frontend**: Storage tab in environments

**Test Steps:**
1. Go to environments page
2. Click "Storage" tab
3. Verify storage buckets display
4. Check storage details

**✅ Success Criteria:**
- All user storage buckets appear
- Storage class displayed correctly  
- Size and object count shown
- Status indicators correct

### Test 6: Create New Storage
**Backend Endpoint**: `POST /storage/create`
**Frontend**: Launch modal → "Create New Workspace"

**Test Steps:**
1. Open launch environment modal
2. Select "Create New Workspace"
3. Choose storage class
4. Launch environment
5. Verify new storage created

**✅ Success Criteria:**
- Storage creation successful
- New bucket appears in list
- Environment uses new storage
- Proper naming convention used

---

## ⚙️ User Settings Tests

### Test 7: Environment Variables
**Backend Endpoints**: 
- `GET /user-env-vars`
- `POST /user-env-vars` 
- `DELETE /user-env-vars/{key}`

**Test Steps:**
1. Go to `/settings`
2. View environment variables section
3. Add new env var: `TEST_KEY=test_value`
4. Edit existing env var
5. Delete env var
6. Verify changes persist

**✅ Success Criteria:**
- All operations complete successfully
- Variables appear in list immediately  
- Changes reflected in new environments
- Proper validation on key/value inputs

### Test 8: File Upload
**Backend Endpoints**:
- `GET /user-files`
- `POST /user-files/upload`
- `DELETE /user-files/{id}`

**Test Steps:**
1. Go to file management section
2. Upload JSON config file
3. Upload GCP credentials file
4. Set environment variable names
5. Set container paths
6. Delete uploaded file

**✅ Success Criteria:**
- Files upload successfully
- Proper file type detection
- Environment variables created
- Files accessible in environments
- Download functionality works

---

## 📊 Real-time Features Tests

### Test 9: Live Environment Monitoring
**Backend**: WebSocket connections (if implemented) or polling
**Frontend**: 10-second refresh interval

**Test Steps:**
1. Open environments page in two browser tabs
2. Create environment in tab 1
3. Watch tab 2 for automatic updates
4. Stop environment in tab 1
5. Verify tab 2 updates status

**✅ Success Criteria:**
- Changes appear in both tabs
- No manual refresh needed
- Status changes reflected quickly
- Resource usage updates

### Test 10: Activity Log
**Backend Endpoint**: `GET /activity`
**Frontend**: Dashboard → Recent Activity

**Test Steps:**
1. Perform several environment actions
2. Go to dashboard
3. Check recent activity section
4. Verify timeline accuracy

**✅ Success Criteria:**
- All actions logged correctly
- Timestamps accurate
- Actions linked to correct user
- Success/failure status shown

---

## 🚨 Error Handling Tests

### Test 11: Network Errors
**Test Scenario**: Backend unavailable

**Test Steps:**
1. Stop backend server
2. Try environment operations
3. Check error handling
4. Restart backend
5. Verify recovery

**✅ Success Criteria:**
- Friendly error messages shown
- No app crashes
- Retry mechanisms work
- Graceful recovery when backend returns

### Test 12: Authentication Errors  
**Test Scenario**: Token expiry

**Test Steps:**
1. Manually expire JWT token
2. Make API calls
3. Verify redirect to login
4. Re-authenticate
5. Resume normal operations

**✅ Success Criteria:**
- Automatic redirect to login
- Token refresh works
- No data loss during re-auth
- Seamless user experience

### Test 13: Validation Errors
**Test Scenario**: Invalid input data

**Test Steps:**
1. Try creating environment with 0 CPU
2. Upload invalid file type  
3. Set invalid environment variables
4. Submit malformed data

**✅ Success Criteria:**
- Form validation prevents submission
- Clear error messages shown
- Backend validation errors displayed
- No console errors

---

## 📱 Responsive Design Tests

### Test 14: Mobile/Tablet View
**Test Different Screen Sizes**

**Test Steps:**
1. Open developer tools
2. Test iPhone/iPad viewports
3. Navigate all pages
4. Test all functionality

**✅ Success Criteria:**
- All pages responsive
- Touch interactions work
- Tables scroll horizontally
- Buttons appropriately sized

---

## ⚡ Performance Tests

### Test 15: Load Testing
**Test Heavy Usage Scenarios**

**Test Steps:**
1. Create 5+ environments rapidly  
2. Navigate between pages quickly
3. Upload multiple files
4. Keep page open for extended time

**✅ Success Criteria:**
- No memory leaks
- Fast page transitions
- API calls properly cached
- Background updates continue

---

## 🔧 Integration Edge Cases

### Test 16: Storage Class Compatibility
**Backend**: Uses uppercase `"STANDARD"` 
**Frontend**: Uses lowercase `"standard"`

**Test Steps:**
1. Create storage with different classes
2. Verify case handling
3. Check display consistency

### Test 17: Date Format Compatibility
**Backend**: ISO format `2024-08-23T10:00:00Z`
**Frontend**: Localized display

**Test Steps:**
1. Create environments at different times
2. Check date display formatting
3. Verify timezone handling
4. Test sorting by date

### Test 18: Multi-Environment Support  
**Backend**: Supports multiple environments per user
**Frontend**: Environment list and switching

**Test Steps:**
1. Create 3+ environments
2. Switch between them
3. Manage each independently  
4. Delete specific environments
5. Verify environment isolation

---

## 🎪 Demo Scenarios

### Scenario A: New User Onboarding
1. **Login** → Google OAuth
2. **Welcome** → Dashboard tour
3. **First Environment** → Launch wizard
4. **File Upload** → Config files
5. **Access Environment** → Open running instance

### Scenario B: Research Workflow  
1. **Setup** → Upload data files
2. **Configure** → Set environment variables
3. **Launch** → Heavy computation environment  
4. **Monitor** → Check resource usage
5. **Scale** → Create additional environments
6. **Cleanup** → Stop and delete when done

### Scenario C: Admin Operations
1. **Multi-Environment** → Create several environments
2. **Batch Operations** → Stop multiple environments
3. **Storage Management** → Organize workspaces
4. **Monitoring** → Real-time status tracking
5. **Maintenance** → Clean up old resources

---

## 🏆 Success Metrics

**Environment Management:** ✅
- Create, list, stop, restart, delete all work
- Real-time updates function correctly
- Resource configurations accurate

**Authentication:** ✅
- OAuth flow seamless
- Token handling secure
- Session persistence works

**File Operations:** ✅
- Upload, download, delete functional
- Environment variable injection works
- File type validation correct

**Storage Management:** ✅
- Bucket operations successful
- Storage class handling consistent
- Integration with environments smooth

**Real-time Features:** ✅
- Auto-refresh working
- Status updates immediate
- Multi-tab sync functional

**Error Handling:** ✅
- Network errors handled gracefully
- Validation errors clear and actionable
- Recovery mechanisms working

---

## 🐛 Common Issues and Solutions

**Issue**: Storage class case mismatch
**Fix**: Normalize to uppercase in API client or backend

**Issue**: Date format inconsistencies  
**Fix**: Ensure consistent timezone handling

**Issue**: CORS errors
**Fix**: Verify backend CORS configuration includes frontend URL

**Issue**: Authentication token not included
**Fix**: Check NextAuth configuration and interceptor setup

**Issue**: Real-time updates not working
**Fix**: Verify React Query configuration and refetch intervals

---

## 📝 Test Report Template

```
Test Session: _____________
Tester: ___________________
Date: ____________________

Environment Management: ⚪ Pass ⚪ Fail ⚪ Partial
Authentication Flow: ⚪ Pass ⚪ Fail ⚪ Partial  
Storage Operations: ⚪ Pass ⚪ Fail ⚪ Partial
File Management: ⚪ Pass ⚪ Fail ⚪ Partial
Real-time Updates: ⚪ Pass ⚪ Fail ⚪ Partial
Error Handling: ⚪ Pass ⚪ Fail ⚪ Partial
Mobile Responsiveness: ⚪ Pass ⚪ Fail ⚪ Partial

Overall Assessment: ⚪ Ready for Production ⚪ Needs Minor Fixes ⚪ Major Issues

Notes:
_________________________________
_________________________________
_________________________________
```

## 🚀 Quick Start Testing

1. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup:**
   ```bash
   cd nextjs-frontend
   npm install
   npm run dev
   ```

3. **Environment Variables:**
   - Copy `.env.example` to `.env.local`
   - Set Google OAuth credentials
   - Set API URL and auth secrets

4. **Test API Health:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8501  
   ```

**Your Next.js frontend should integrate seamlessly with your FastAPI backend! 🎉**
