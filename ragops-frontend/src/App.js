import React, { useState } from 'react';
import axios from 'axios';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { styled, keyframes } from '@mui/system';
import { Button, TextField, Typography, Paper, List, ListItem, ListItemText, CircularProgress, Box } from '@mui/material';
import { Science, Lightbulb, Search } from '@mui/icons-material';
import { motion, useAnimation } from 'framer-motion';
import { useSpring, animated } from '@react-spring/web';
import { ParallaxProvider, Parallax } from 'react-scroll-parallax';
import { useInView } from 'react-intersection-observer';

const theme = createTheme({
  palette: {
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#e0e0e0',
      paper: 'rgba(255, 255, 255, 0.9)',
    },
    text: {
      primary: '#333',
    },
  },
  typography: {
    fontFamily: '"Playfair Display", serif',
    h1: {
      fontSize: '4rem',
      fontWeight: 700,
      color: '#C8A2C8', // Lilac color
      textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
    },
    h5: {
      fontWeight: 600,
    },
  },
});

const AppContainer = styled('div')({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '2rem',
  minHeight: '100vh',
  position: 'relative',
  zIndex: 1,
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    background: 'linear-gradient(to bottom, #87CEEB, #E0F2F7)',
    zIndex: -1,
  },
});

const cloudAnimation1 = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100vw); }
`;

const cloudAnimation2 = keyframes`
  0% { transform: translateX(100vw); }
  100% { transform: translateX(-100%); }
`;

const Cloud = styled('div')(({ top, animationDuration, size }) => ({
  position: 'absolute',
  width: size,
  height: size * 0.6,
  background: '#fff',
  borderRadius: '50%',
  top: top,
  opacity: 0.7,
  '&::before, &::after': {
    content: '""',
    position: 'absolute',
    background: '#fff',
    borderRadius: '50%',
  },
  '&::before': {
    width: size * 0.36,
    height: size * 0.36,
    top: size * -0.22,
    left: size * 0.03,
  },
  '&::after': {
    width: size * 0.48,
    height: size * 0.48,
    top: size * -0.24,
    right: size * 0.1,
  },
  animation: `${cloudAnimation1} ${animationDuration}s linear infinite`,
}));

const ReversedCloud = styled(Cloud)({
  animation: `${cloudAnimation2} ${props => props.animationDuration}s linear infinite`,
});

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginTop: theme.spacing(3),
  maxWidth: 600,
  width: '100%',
  backdropFilter: 'blur(10px)',
  backgroundColor: 'rgba(255, 255, 255, 0.8)',
  borderRadius: '15px',
  boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
}));

const StyledForm = styled('form')({
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
});

const FancyHeader = styled(Typography)(({ theme }) => ({
  background: '#00008B', // Lilac gradient
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  padding: '20px',
  borderRadius: '10px',
  boxShadow: '0 3px 5px 2px rgba(200, 162, 200, .3)',
  textAlign: 'center',
  marginBottom: '2rem',
}));

const AnimatedIcon = ({ Icon }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.2, rotate: 10 }}
      whileTap={{ scale: 0.8, rotate: -10 }}
    >
      <Icon fontSize="large" color="primary" />
    </motion.div>
  );
};

const AnimatedText = ({ children }) => {
  const controls = useAnimation();
  const [ref, inView] = useInView();

  React.useEffect(() => {
    if (inView) {
      controls.start({ opacity: 1, y: 0 });
    }
  }, [controls, inView]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      transition={{ duration: 0.5 }}
      whileHover={{ scale: 1.05, color: '#3f51b5' }}
    >
      {children}
    </motion.div>
  );
};

function App() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await axios.post('https://77ywt7l8yd.execute-api.us-east-1.amazonaws.com/prod/recommend', { question });
      const parsedBody = JSON.parse(result.data.body);
      setResponse(parsedBody);
    } catch (err) {
      console.error('Error:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fadeIn = useSpring({
    opacity: response ? 1 : 0,
    transform: response ? 'translateY(0)' : 'translateY(50px)',
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ParallaxProvider>
        <AppContainer>
          <Cloud top="10%" animationDuration={60} size={100} />
          <ReversedCloud top="30%" animationDuration={75} size={150} />
          <Cloud top="60%" animationDuration={90} size={120} />
          <Parallax speed={-5}>
            <motion.div
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <FancyHeader variant="h1" component="h1" gutterBottom>
                RAGOps Product Recommender
              </FancyHeader>
            </motion.div>
          </Parallax>
          
          <Parallax speed={5}>
            <StyledPaper elevation={3}>
              <Box display="flex" justifyContent="center" mb={2}>
                <AnimatedIcon Icon={Science} />
              </Box>
              <StyledForm onSubmit={handleSubmit}>
                <TextField
                  label="Enter your question"
                  variant="outlined"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  required
                  fullWidth
                />
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Search />}
                  size="large"
                >
                  {loading ? 'Searching...' : 'Get Answer'}
                </Button>
              </StyledForm>
            </StyledPaper>
          </Parallax>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Typography color="error" style={{ marginTop: '1rem', backgroundColor: 'rgba(255,255,255,0.8)', padding: '0.5rem', borderRadius: '5px' }}>
                {error}
              </Typography>
            </motion.div>
          )}

          {response && (
            <Parallax speed={10}>
              <animated.div style={fadeIn}>
                <StyledPaper elevation={3} style={{ marginTop: '2rem' }}>
                  <Box display="flex" justifyContent="center" mb={2}>
                    <AnimatedIcon Icon={Lightbulb} />
                  </Box>
                  <AnimatedText>
                    <Typography variant="h5" gutterBottom>
                      Answer:
                    </Typography>
                  </AnimatedText>
                  <AnimatedText>
                    <Typography paragraph>{response.answer}</Typography>
                  </AnimatedText>

                  <AnimatedText>
                    <Typography variant="h6" gutterBottom>
                      Keywords:
                    </Typography>
                  </AnimatedText>
                  <List>
                    {response.keywords.map((keyword, index) => (
                      <ListItem key={index}>
                        <motion.div
                          initial={{ opacity: 0, x: -50 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.5, delay: index * 0.1 }}
                        >
                          <ListItemText primary={keyword} />
                        </motion.div>
                      </ListItem>
                    ))}
                  </List>

                  <AnimatedText>
                    <Typography>
                      Number of relevant products found: {response.num_results}
                    </Typography>
                  </AnimatedText>
                </StyledPaper>
              </animated.div>
            </Parallax>
          )}
        </AppContainer>
      </ParallaxProvider>
    </ThemeProvider>
  );
}

export default App;