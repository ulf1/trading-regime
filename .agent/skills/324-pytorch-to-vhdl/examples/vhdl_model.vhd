library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity vhdl_model is
    port (
        clk    : in  std_logic;
        reset  : in  std_logic;
        start  : in  std_logic;
        input  : in  signed(15 downto 0);  -- Q8.8 fixed-point (16 bits)
        output : out signed(15 downto 0);  -- Q8.8 fixed-point (16 bits)
        done   : out std_logic
    );
end entity;

architecture rtl of vhdl_model is
    -- Internal fixed-point signals
    signal acc : signed(31 downto 0) := (others => '0'); -- Accumulator (extended for multiplication)
    
    -- Weights (Extracted from PyTorch)
    -- This constant array should be generated from Python quantization scripts
    type weight_array is array (0 to 7) of signed(15 downto 0);
    constant layer1_weights : weight_array := (
        to_signed(256, 16),   -- 1.0 in Q8.8
        to_signed(-128, 16),  -- -0.5 in Q8.8
        others => to_signed(0, 16)
    );
    
    -- State machine definition
    type state_type is (IDLE, COMPUTE, FINISH);
    signal current_state : state_type := IDLE;
    signal counter       : integer range 0 to 7 := 0;

begin
    process(clk, reset)
    begin
        if reset = '1' then
            acc <= (others => '0');
            output <= (others => '0');
            done <= '0';
            current_state <= IDLE;
            counter <= 0;
        elsif rising_edge(clk) then
            case current_state is
                when IDLE =>
                    done <= '0';
                    if start = '1' then
                        acc <= (others => '0');
                        counter <= 0;
                        current_state <= COMPUTE;
                    end if;
                
                when COMPUTE =>
                    -- Multiply-Accumulate logic
                    -- acc <= acc + (input * weight)
                    acc <= acc + (input * layer1_weights(counter));
                    
                    if counter = 7 then
                        current_state <= FINISH;
                    else
                        counter <= counter + 1;
                    end if;
                
                when FINISH =>
                    -- Scaling back to Q8.8 (shift right by 8)
                    output <= acc(23 downto 8); -- Q8.8 = bits [23:8] of 32-bit Q16.16 product
                    done <= '1';
                    current_state <= IDLE;
                
                when others =>
                    current_state <= IDLE;
            end case;
        end if;
    end process;
end architecture;
