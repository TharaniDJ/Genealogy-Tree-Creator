import React from 'react';
import styled from 'styled-components';

interface StyledIconBoxProps {
  children: React.ReactNode;
  variant?: 'purple' | 'blue' | 'green' | 'default';
  size?: 'sm' | 'md' | 'lg';
}

const StyledIconBox: React.FC<StyledIconBoxProps> = ({ 
  children, 
  variant = 'default',
  size = 'md'
}) => {
  return (
    <StyledWrapper variant={variant} size={size}>
      <div className="icon-box">
        {children}
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div<{ variant: string; size: string }>`
  .icon-box {
    /* Color variants */
    ${props => {
      switch (props.variant) {
        case 'purple':
          return `
            --main-color: rgb(139, 123, 255);
            --main-bg-color: rgba(139, 123, 255, 0.36);
            --pattern-color: rgba(139, 123, 255, 0.073);
          `;
        case 'blue':
          return `
            --main-color: rgb(59, 130, 246);
            --main-bg-color: rgba(59, 130, 246, 0.36);
            --pattern-color: rgba(59, 130, 246, 0.073);
          `;
        case 'green':
          return `
            --main-color: rgb(34, 197, 94);
            --main-bg-color: rgba(34, 197, 94, 0.36);
            --pattern-color: rgba(34, 197, 94, 0.073);
          `;
        default:
          return `
            --main-color: rgb(107, 114, 255);
            --main-bg-color: rgba(107, 114, 255, 0.36);
            --pattern-color: rgba(107, 114, 255, 0.073);
          `;
      }
    }}

    /* Size variants */
    ${props => {
      switch (props.size) {
        case 'sm':
          return `
            width: 2.5rem;
            height: 2.5rem;
          `;
        case 'lg':
          return `
            width: 5rem;
            height: 5rem;
          `;
        default: // md
          return `
            width: 3.5rem;
            height: 3.5rem;
          `;
      }
    }}

    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(
        circle,
        var(--main-bg-color) 0%,
        rgba(0, 0, 0, 0) 95%
      ),
      linear-gradient(var(--pattern-color) 1px, transparent 1px),
      linear-gradient(to right, var(--pattern-color) 1px, transparent 1px);
    background-size:
      cover,
      15px 15px,
      15px 15px;
    background-position:
      center center,
      center center,
      center center;
    border-image: radial-gradient(
        circle,
        var(--main-color) 0%,
        rgba(0, 0, 0, 0) 100%
      )
      1;
    border-width: 1px 0 1px 0;
    border-style: solid;
    color: var(--main-color);
    transition: all 0.2s ease-in-out;
    border-left: none;
    border-right: none;

    svg {
      color: var(--main-color);
    }
  }

  .icon-box:hover {
    background-size:
      cover,
      10px 10px,
      10px 10px;
  }
`;

export default StyledIconBox;
