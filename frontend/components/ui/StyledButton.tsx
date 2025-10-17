import React from 'react';
import styled from 'styled-components';

interface StyledButtonProps {
  onClick?: (e: React.MouseEvent) => void;
  children: React.ReactNode;
  variant?: 'purple' | 'blue' | 'green' | 'red';
  className?: string;
}

const StyledButton: React.FC<StyledButtonProps> = ({ 
  onClick, 
  children, 
  variant = 'purple',
  className 
}) => {
  return (
    <StyledWrapper variant={variant} className={className}>
      <button className="button" onClick={onClick}>
        {children}
      </button>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div<{ variant: 'purple' | 'blue' | 'green' | 'red' }>`
  width: 100%;
  
  .button {
    cursor: pointer;
    position: relative;
    padding: 10px 24px;
    font-size: 18px;
    ${props => {
      switch (props.variant) {
        case 'purple':
          return `
            color: rgb(139, 123, 255);
            border: 2px solid rgb(139, 123, 255);
            &::before {
              background-color: rgb(139, 123, 255);
            }
            &:hover {
              box-shadow: 0 0px 20px rgba(139, 123, 255, 0.4);
            }
          `;
        case 'blue':
          return `
            color: rgb(59, 130, 246);
            border: 2px solid rgb(59, 130, 246);
            &::before {
              background-color: rgb(59, 130, 246);
            }
            &:hover {
              box-shadow: 0 0px 20px rgba(59, 130, 246, 0.4);
            }
          `;
        case 'green':
          return `
            color: rgb(34, 197, 94);
            border: 2px solid rgb(34, 197, 94);
            &::before {
              background-color: rgb(34, 197, 94);
            }
            &:hover {
              box-shadow: 0 0px 20px rgba(34, 197, 94, 0.4);
            }
          `;
        case 'red':
          return `
            color: rgb(239, 68, 68);
            border: 2px solid rgb(239, 68, 68);
            &::before {
              background-color: rgb(239, 68, 68);
            }
            &:hover {
              box-shadow: 0 0px 20px rgba(239, 68, 68, 0.4);
            }
          `;
      }
    }}
    border-radius: 34px;
    background-color: transparent;
    font-weight: 600;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.320, 1);
    overflow: hidden;
    width: 100%;
  }

  .button::before {
    content: '';
    position: absolute;
    inset: 0;
    margin: auto;
    width: 50px;
    height: 50px;
    border-radius: inherit;
    scale: 0;
    z-index: -1;
    transition: all 0.6s cubic-bezier(0.23, 1, 0.320, 1);
  }

  .button:hover::before {
    scale: 6;
  }

  .button:hover {
    color: #212121;
    scale: 1.0;
  }

  .button:active {
    scale: 1;
  }
`;

export default StyledButton;
