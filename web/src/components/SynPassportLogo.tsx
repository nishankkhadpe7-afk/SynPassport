import React from "react";

interface SynPassportLogoProps {
  size?: number;
  className?: string;
}

export const SynPassportLogo: React.FC<SynPassportLogoProps> = ({
  size = 36,
  className = "",
}) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      className={className}
    >
      <rect width="48" height="48" rx="8" fill="#121821" stroke="#232A33" strokeWidth="1.5" />
      <path
        d="M24 8L36 13V23C36 30.5 30.9 37.4 24 40C17.1 37.4 12 30.5 12 23V13L24 8Z"
        fill="#0B131E"
        stroke="#2DD4BF"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M24 16V24M24 24L29 27M24 24L19 27"
        stroke="#34D399"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle cx="24" cy="24" r="3" fill="#2DD4BF" />
      <path
        d="M20 28L23 31L28 25"
        stroke="#F9FAFB"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="36" cy="13" r="2" fill="#2DD4BF" />
    </svg>
  );
};
