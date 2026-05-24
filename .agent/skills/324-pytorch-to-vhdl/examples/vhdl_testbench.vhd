library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity vhdl_testbench is
end entity;

architecture test of vhdl_testbench is
    -- Signal declarations
    signal clk, reset, start, done : std_logic := '0';
    signal input, output : signed(15 downto 0) := (others => '0');
    constant CLK_PERIOD  : time := 10 ns;
begin
    -- Unit Under Test (UUT)
    uut: entity work.vhdl_model
        port map (
            clk    => clk,
            reset  => reset,
            start  => start,
            input  => input,
            output => output,
            done   => done
        );

    -- Clock Generation
    clk <= not clk after CLK_PERIOD / 2;

    -- Stimulus Process
    stim: process
    begin
        -- Reset Sequence
        reset <= '1';
        wait for CLK_PERIOD * 2;
        reset <= '0';
        wait for CLK_PERIOD;
        
        -- Stimulus: 1.0 (256) in Q8.8
        input <= to_signed(256, 16);
        start <= '1';
        wait for CLK_PERIOD;
        start <= '0';
        
        -- Wait until inference finishes
        wait until done = '1';
        
        -- Report Output: (Expected: 1.0 * 1.0 + 1.0 * -0.5 = 0.5 = 128)
        report "Simulation Finished. Output: " & integer'image(to_integer(output));
        
        wait for CLK_PERIOD * 10;
        
        -- Finish simulation
        wait;
    end process;
end architecture;
