# Email Campaign System Implementation Plan

## Context
Building an email campaign system for VortexHealing Admin Dashboard to enable:
1. **Phase 1**: Email Campaign System - Compose emails and segment Student contacts by tags/lists
2. **Phase 2**: Email Scheduling - Use Qwen AI to draft and schedule emails

## Current State

### Backend Status
✅ **COMPLETE** - Email Campaign System Phase 1 backend is done:
- `backend/app/models.py` - EmailCampaign and EmailRecipient models added
- `backend/app/api/email_campaigns.py` - All 5 endpoints implemented:
  - `POST /api/email/campaigns` - Create campaign
  - `GET /api/email/campaigns` - List campaigns
  - `POST /api/email/preview` - Preview recipients
  - `POST /api/email/send` - Send campaign
  - `GET /api/students/filter` - Filter by tags/lists

### Frontend Status
⏳ **TODO** - Email.tsx needs to be built

---

## Frontend Implementation (Phase 1)

### File to Edit
`frontend/src/pages/Email.tsx`

### Components to Build

**1. Campaign Composer Modal**
- Title input
- Subject input
- Body textarea
- Tag/List selector dropdown
- Preview button
- Save as Draft button

**2. Recipient Preview**
- Shows count: "X students match your filters"
- Shows 3-5 sample recipients with names/emails

**3. Send Confirmation Modal**
- Exact recipient count
- Sample recipients list
- "Send Now" and "Cancel" buttons

**4. Campaign History Table**
- Columns: Title, Subject, Recipients, Status, Date
- Status badges: green=sent, yellow=draft, red=failed
- Clickable rows to view details

### Styling Guidelines
- **Primary color**: `#667eea`
- **All inline styles** (no Tailwind)
- **Modal shadow**: `0 4px 20px rgba(0,0,0,0.2)`
- **Button padding**: `0.75rem 1.5rem`
- **Icons**: Lucide (Mail, Send, Filter, Tag)

### Reference Pattern
Follow `frontend/src/pages/Tasks.tsx` for:
- Modal structure
- Button styling
- State management with React Query
- Axios API calls

### API Endpoints to Call
```javascript
// Create campaign
POST /api/email/campaigns
{ title, subject, body, recipient_tags, recipient_lists }

// Get all campaigns
GET /api/email/campaigns

// Preview recipients
POST /api/email/preview
{ title, subject, body, recipient_tags, recipient_lists }

// Send campaign
POST /api/email/send
{ campaign_id }

// Filter students by tags/lists
GET /api/students/filter?tags=Active&lists=APAC Wizards
```

### State Management Example
```typescript
const [showComposer, setShowComposer] = useState(false);
const [showPreview, setShowPreview] = useState(false);
const [title, setTitle] = useState('');
const [subject, setSubject] = useState('');
const [body, setBody] = useState('');
const [selectedTags, setSelectedTags] = useState('');
const [selectedLists, setSelectedLists] = useState('');
const [previewData, setPreviewData] = useState(null);

const { data: campaigns } = useQuery('campaigns', () =>
  axios.get('/api/email/campaigns').then(r => r.data)
);

const handlePreview = async () => {
  const preview = await axios.post('/api/email/preview', {
    title, subject, body, 
    recipient_tags: selectedTags,
    recipient_lists: selectedLists
  });
  setPreviewData(preview.data);
  setShowPreview(true);
};

const handleSend = async (campaignId) => {
  await axios.post('/api/email/send', { campaign_id: campaignId });
  // Refresh campaigns
};
```

---

## Phase 2: Qwen Integration (Future)

When Phase 1 is complete, add:
1. "Generate with Qwen" button in composer
2. Qwen draft suggestions panel
3. Date/time picker for scheduling
4. "Schedule for Later" button
5. Background scheduler for timed sends

API endpoint to call:
```
POST /api/email/generate-draft
{ topic, recipient_count, class_name }
```

---

## Testing Checklist

- [ ] Create campaign with title, subject, body
- [ ] Select tags/lists and verify recipient count changes
- [ ] Preview shows 3-5 sample recipients
- [ ] Click "Send Now" and verify campaign appears in history with "sent" status
- [ ] Campaign history shows all past campaigns
- [ ] Filter by different tags/lists combinations

---

## Quick Start with Continue

1. In VS Code, open Continue (Cmd+J)
2. Paste this into the Continue chat:

```
@docs/EMAIL_CAMPAIGN_PLAN.md
@codebase

Build the Email.tsx component following this plan. Use inline styles with primary color #667eea. Follow the modal pattern from Tasks.tsx. Connect to the backend email campaign API endpoints.
```

3. Qwen will generate the complete Email.tsx file
4. Review and make any adjustments
5. Run `npm run dev` and test at http://localhost:5173/email

---

**Status**: Ready to build  
**Backend**: ✅ Complete  
**Frontend**: ⏳ Ready for implementation
