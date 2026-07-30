import { Routes, Route } from "react-router-dom";
import Container from "@mui/material/Container";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TopicEntryView from "./views/TopicEntryView.jsx";
import InterviewView from "./views/InterviewView.jsx";
import SummaryView from "./views/SummaryView.jsx";

export default function App() {
  return (
    <Container maxWidth="sm">
      <Box sx={{ py: 6 }}>
        <Typography variant="h4" component="h1" fontWeight={600} gutterBottom>
          AI Interviewer
        </Typography>
        <Routes>
          <Route path="/" element={<TopicEntryView />} />
          <Route path="/interview/:id" element={<InterviewView />} />
          <Route path="/interview/:id/summary" element={<SummaryView />} />
        </Routes>
      </Box>
    </Container>
  );
}
