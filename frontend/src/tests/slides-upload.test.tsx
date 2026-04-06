import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Home from "@/app/page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => ({
  generateStudyPackFromSlides: jest.fn(),
  generateStudyPack: jest.fn(),
  generateFlashcards: jest.fn(),
  generateQuizQuestions: jest.fn(),
  regenerateSlideQuizQuestions: jest.fn(),
  requestQuizExplanation: jest.fn(),
  submitFlashcardReview: jest.fn(),
  submitFlashcardSessionComplete: jest.fn(),
  submitQuiz: jest.fn(),
  submitQuizResult: jest.fn(),
}));

const mockAuthState: { user: { id: string } | null } = { user: null };

jest.mock("@/context/auth-context", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("@/lib/supabase", () => ({
  supabase: {
    from: jest.fn(() => ({
      insert: jest.fn().mockResolvedValue({ error: null }),
    })),
  },
}));

const mockGenerateStudyPackFromSlides =
  api.generateStudyPackFromSlides as jest.MockedFunction<
    typeof api.generateStudyPackFromSlides
  >;

const slideStudyPackResponse = {
  file_name: "lecture.pdf",
  stored_path: "/tmp/lecture.pdf",
  summary: ["Point one", "Point two"],
  quiz_set_id: "quiz-set-1",
  flashcard_set_id: "flash-set-1",
  extracted_text: "Extracted lecture content.",
  quiz: [
    {
      question: "What is HTTP?",
      options: ["Protocol", "Browser", "Database", "Language"],
      answer: "Protocol",
      topic: "Web",
      correctionExplanation: "HTTP is an application layer protocol.",
    },
  ],
  flashcards: [
    {
      question: "Define HTTP.",
      answer: "Hypertext Transfer Protocol.",
    },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, "error").mockImplementation(() => {});
  mockAuthState.user = { id: "user-1" };
  (api.generateStudyPack as jest.Mock).mockResolvedValue({ summary: [], quiz: [] });
  (api.generateFlashcards as jest.Mock).mockResolvedValue({
    flashcard_set_id: "preview",
    flashcards: [],
  });
});

describe("slides upload flow", () => {
  it("requires login before uploading slides", async () => {
    mockAuthState.user = null;
    const { container } = render(<Home />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["pdf-content"], "lecture.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Please log in to upload slides.",
      );
      expect(mockGenerateStudyPackFromSlides).not.toHaveBeenCalled();
    });
  });

  it("uploads slides and renders generated study content", async () => {
    mockGenerateStudyPackFromSlides.mockResolvedValueOnce(slideStudyPackResponse);
    const { container } = render(<Home />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["pdf-content"], "lecture.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockGenerateStudyPackFromSlides).toHaveBeenCalledTimes(1);
      expect(
        screen.getByText("Uploaded lecture.pdf and generated study content."),
      ).toBeInTheDocument();
      expect(screen.getByText("Your study pack")).toBeInTheDocument();
      expect(screen.getByText("Point one")).toBeInTheDocument();
      expect(screen.queryByDisplayValue("Extracted lecture content.")).not.toBeInTheDocument();
    });
  });

  it("shows processing state while upload is in-flight", async () => {
    let resolveUpload: (value: typeof slideStudyPackResponse) => void = () => {};
    mockGenerateStudyPackFromSlides.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveUpload = resolve;
        }),
    );
    const { container } = render(<Home />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["pptx-content"], "deck.pptx", {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });

    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByRole("button", { name: "Processing..." })).toBeDisabled();

    resolveUpload(slideStudyPackResponse);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Upload slides" })).toBeInTheDocument();
    });
  });

  it("handles upload failure gracefully with user-friendly message", async () => {
    mockGenerateStudyPackFromSlides.mockRejectedValueOnce(
      new TypeError("Failed to fetch"),
    );
    const { container } = render(<Home />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["broken"], "lecture.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Something went wrong. Please try again.",
      );
    });
  });
});
